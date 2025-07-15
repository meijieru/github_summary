import re
import requests
import logging
from datetime import datetime, UTC
from typing import Any
from collections.abc import Callable

logger = logging.getLogger(__name__)

from github_summary.models import Commit, Discussion, FilterConfig, Issue, PullRequest, RepoConfig
from github_summary.queries import (
    GET_ALL_LABELS_QUERY,
    GET_COMMITS_QUERY,
    GET_DISCUSSIONS_QUERY,
    GET_ISSUES_QUERY,
    GET_PULL_REQUESTS_QUERY,
)


class GraphQLClient:
    def __init__(self, token: str):
        """Initializes the GraphQLClient with a GitHub personal access token.

        Args:
            token: The GitHub personal access token.
        """
        self.url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Executes a GraphQL query.

        Args:
            query: The GraphQL query string.
            variables: Optional. A dictionary of variables for the query.

        Returns:
            The JSON response from the GraphQL API.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        logger.debug("Executing GraphQL query:\nQuery: %s\nVariables: %s", query, variables)
        response = requests.post(self.url, json={"query": query, "variables": variables}, headers=self.headers)
        response.raise_for_status()
        logger.debug("GraphQL query response: %s", response.json())
        return response.json()

    def _paginate(
        self,
        query: str,
        variables: dict[str, Any],
        data_extractor: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Paginates through GraphQL query results.

        Args:
            query: The GraphQL query string.
            variables: A dictionary of variables for the query, including pagination cursors.
            data_extractor: A callable that extracts the relevant data (nodes and pageInfo) from the GraphQL response.

        Returns:
            A list of all nodes retrieved through pagination.
        """
        all_nodes = []
        has_next_page = True
        cursor = None

        i = 0
        # TODO(meijierun): Remove the limit of 5 pages.
        while has_next_page and i < 5:
            variables["cursor"] = cursor
            data = self._execute(query, variables)
            page_data = data_extractor(data)
            all_nodes.extend(page_data["nodes"])
            has_next_page = page_data["pageInfo"]["hasNextPage"]
            cursor = page_data["pageInfo"]["endCursor"]
            i += 1

        return all_nodes


class GitHubService:
    def __init__(self, token: str):
        """Initializes the GitHubService with a personal access token.

        Args:
            token: The GitHub personal access token.
        """
        self.client = GraphQLClient(token)

    def get_commits(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[Commit]:
        """Fetches commits for a given repository, applying specified filters.

        Args:
            repo: The repository configuration.
            filters: The filter configuration to apply.
            since: The datetime from which to fetch commits.

        Returns:
            A list of Commit objects.
        """
        if not repo.include_commits:
            return []

        owner, repo_name = repo.name.split("/")
        variables: dict[str, Any] = {"owner": owner, "repo": repo_name}

        commits_data = self.client._paginate(
            GET_COMMITS_QUERY,
            variables,
            lambda data: data["data"]["repository"]["defaultBranchRef"]["target"]["history"],
        )

        filtered_commits = []
        for item in commits_data:
            commit_date = datetime.fromisoformat(item["author"]["date"]).astimezone(UTC)
            if commit_date < since:
                continue
            if filters.commits:
                if filters.commits.author and item["author"]["name"] != filters.commits.author:
                    continue
                if filters.commits.exclude_commit_messages_regex and re.search(
                    filters.commits.exclude_commit_messages_regex, item["messageHeadline"]
                ):
                    continue
            filtered_commits.append(
                Commit(
                    sha=item["oid"],
                    author=item["author"]["name"],
                    message=item["messageHeadline"],
                    date=item["author"]["date"],
                    html_url=item["url"],
                )
            )
        return filtered_commits

    def get_pull_requests(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[PullRequest]:
        """Fetches pull requests for a given repository, applying specified filters.

        Args:
            repo: The repository configuration.
            filters: The filter configuration to apply.
            since: The datetime from which to fetch pull requests.

        Returns:
            A list of PullRequest objects.
        """
        if not repo.include_pull_requests:
            return []

        owner, repo_name = repo.name.split("/")
        variables: dict[str, Any] = {"owner": owner, "repo": repo_name}
        if filters.pull_requests:
            if filters.pull_requests.state:
                variables["state"] = filters.pull_requests.state
            if filters.pull_requests.labels:
                variables["labels"] = filters.pull_requests.labels

        pull_requests_data = self.client._paginate(
            GET_PULL_REQUESTS_QUERY,
            variables,
            lambda data: data["data"]["repository"]["pullRequests"],
        )

        filtered_pull_requests = []
        for item in pull_requests_data:
            pr_date_str = (
                item["updatedAt"] if filters.pull_requests.since_filter_type == "updated" else item["createdAt"]
            )
            pr_date = datetime.fromisoformat(pr_date_str).astimezone(UTC)
            if pr_date < since:
                continue

            if (
                filters.pull_requests
                and filters.pull_requests.author
                and item["author"]["login"] != filters.pull_requests.author
            ):
                continue
            if filters.pull_requests and filters.pull_requests.exclude_pull_request_titles_regex:
                if re.search(filters.pull_requests.exclude_pull_request_titles_regex, item["title"]):
                    continue
            pr_labels = [label["name"] for label in item.get("labels", {}).get("nodes", [])]
            filtered_pull_requests.append(
                PullRequest(
                    number=item["number"],
                    title=item["title"],
                    author=item["author"]["login"] if item["author"] else "Unknown",
                    state=item["state"],
                    created_at=item["createdAt"],
                    merged_at=item["mergedAt"],
                    html_url=item["url"],
                    labels=pr_labels,
                )
            )
        return filtered_pull_requests

    def get_issues(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[Issue]:
        """Fetches issues for a given repository, applying specified filters.

        Args:
            repo: The repository configuration.
            filters: The filter configuration to apply.
            since: The datetime from which to fetch issues.

        Returns:
            A list of Issue objects.
        """
        if not repo.include_issues:
            return []

        owner, repo_name = repo.name.split("/")
        query_parts = [
            f"repo:{owner}/{repo_name}",
            "is:issue",
            f"created:>{since.isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        ]
        if filters.issues.type:
            query_parts.append(f'label:"{filters.issues.type}"')

        search_query = " ".join(query_parts)
        variables: dict[str, Any] = {"searchQuery": search_query}

        issues_data = self.client._paginate(
            GET_ISSUES_QUERY,
            variables,
            lambda data: data["data"]["search"],
        )

        filtered_issues = []
        for item in issues_data:
            if filters.issues and filters.issues.exclude_issue_titles_regex:
                if re.search(filters.issues.exclude_issue_titles_regex, item["title"]):
                    continue
            issue_labels = [label["name"] for label in item.get("labels", {}).get("nodes", [])]
            filtered_issues.append(
                Issue(
                    number=item["number"],
                    title=item["title"],
                    author=item["author"]["login"] if item["author"] else "Unknown",
                    state=item["state"],
                    created_at=item["createdAt"],
                    html_url=item["url"],
                    labels=issue_labels,
                )
            )
        return filtered_issues

    def get_discussions(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[Discussion]:
        """Fetches discussions for a given repository, applying specified filters.

        Args:
            repo: The repository configuration.
            filters: The filter configuration to apply.
            since: The datetime from which to fetch discussions.

        Returns:
            A list of Discussion objects.
        """
        if not repo.include_discussions:
            return []

        owner, repo_name = repo.name.split("/")
        variables: dict[str, Any] = {"owner": owner, "repo": repo_name}

        discussions_data = self.client._paginate(
            GET_DISCUSSIONS_QUERY,
            variables,
            lambda data: data["data"]["repository"]["discussions"],
        )

        filtered_discussions = []
        for item in discussions_data:
            discussion_date = datetime.fromisoformat(item["createdAt"]).astimezone(UTC)
            if discussion_date < since:
                continue
            if filters.discussions.author and item["author"]["login"] != filters.discussions.author:
                continue
            if filters.discussions.exclude_discussion_titles_regex and re.search(
                filters.discussions.exclude_discussion_titles_regex, item["title"]
            ):
                continue
            filtered_discussions.append(
                Discussion(
                    id=item["id"],
                    title=item["title"],
                    author=item["author"]["login"] if item["author"] else "Unknown",
                    created_at=item["createdAt"],
                    html_url=item["url"],
                )
            )
        return filtered_discussions

    def get_all_labels(self, owner: str, repo_name: str) -> list[str]:
        """Fetches all labels for a given repository.

        Args:
            owner: The owner of the repository.
            repo_name: The name of the repository.

        Returns:
            A list of label names.
        """
        variables: dict[str, Any] = {"owner": owner, "name": repo_name}
        labels_data = self.client._paginate(
            GET_ALL_LABELS_QUERY,
            variables,
            lambda data: data["data"]["repository"]["labels"],
        )
        return [label["name"] for label in labels_data]
