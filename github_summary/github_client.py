"""GitHub service using gidgethub for HTTP handling with domain-specific business logic"""

import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
from gidgethub.httpx import GitHubAPI

from github_summary.models import Commit, Discussion, FilterConfig, Issue, PullRequest, RepoConfig
from github_summary.queries import (
    GET_ALL_LABELS_QUERY,
    GET_COMMITS_QUERY,
    GET_DISCUSSIONS_QUERY,
    GET_ISSUES_QUERY,
    GET_PULL_REQUESTS_QUERY,
)

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self, token: str, user_agent: str = "github-summary/1.0"):
        """Initialize the enhanced GitHub service.

        Args:
            token: GitHub personal access token
            user_agent: User agent string for requests
        """
        self.token = token
        self.user_agent = user_agent
        self.session: httpx.AsyncClient | None = None
        self.gh_client: GitHubAPI | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(timeout=30.0)
        self.gh_client = GitHubAPI(client=self.session, requester=self.user_agent, oauth_token=self.token)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    @property
    def rate_limit(self):
        """Access gidgethub's rate limit information."""
        return self.gh_client.rate_limit if self.gh_client else None

    async def get_commits(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[Commit]:
        """Fetch commits with our exact same API and business logic.

        Args:
            repo: Repository configuration
            filters: Filter configuration
            since: Datetime to fetch commits since

        Returns:
            List of Commit objects
        """
        if not repo.include_commits:
            return []

        owner, repo_name = repo.name.split("/")
        variables: dict[str, Any] = {"owner": owner, "repo": repo_name}

        # Use gidgethub for HTTP (automatic rate limiting + caching + retries)
        commits_data = await self._paginate_graphql(
            GET_COMMITS_QUERY,
            variables,
            lambda data: data["repository"]["defaultBranchRef"]["target"]["history"],
        )

        # Keep our exact same filtering and model conversion logic
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

    async def get_pull_requests(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[PullRequest]:
        """Fetch pull requests with our exact same API and business logic."""
        if not repo.include_pull_requests:
            return []

        owner, repo_name = repo.name.split("/")
        variables: dict[str, Any] = {"owner": owner, "repo": repo_name}
        if filters.pull_requests:
            if filters.pull_requests.state:
                variables["state"] = filters.pull_requests.state
            if filters.pull_requests.labels:
                variables["labels"] = filters.pull_requests.labels

        pull_requests_data = await self._paginate_graphql(
            GET_PULL_REQUESTS_QUERY,
            variables,
            lambda data: data["repository"]["pullRequests"],
        )

        filtered_pull_requests = []
        for item in pull_requests_data:
            pr_date_str = (
                item["updatedAt"] if filters.pull_requests.since_filter_type == "updated" else item["createdAt"]
            )
            pr_date = datetime.fromisoformat(pr_date_str).astimezone(UTC)
            if pr_date < since:
                continue

            if filters.pull_requests:
                if (
                    filters.pull_requests.author
                    and item["author"]
                    and item["author"]["login"] != filters.pull_requests.author
                ):
                    continue
                if filters.pull_requests.state and item["state"] != filters.pull_requests.state:
                    continue
                if filters.pull_requests.labels:
                    pr_labels = [label["name"] for label in item.get("labels", {}).get("nodes", [])]
                    if not all(label in pr_labels for label in filters.pull_requests.labels):
                        continue
                if filters.pull_requests.exclude_pull_request_titles_regex:
                    if re.search(filters.pull_requests.exclude_pull_request_titles_regex, item["title"]):
                        continue

            pr_labels = [label["name"] for label in item.get("labels", {}).get("nodes", [])]
            filtered_pull_requests.append(
                PullRequest(
                    number=item["number"],
                    title=item["title"],
                    body=item["body"],
                    author=item["author"]["login"] if item["author"] else "Unknown",
                    state=item["state"],
                    created_at=item["createdAt"],
                    updated_at=item["updatedAt"],
                    merged_at=item["mergedAt"],
                    html_url=item["url"],
                    labels=pr_labels,
                )
            )
        return filtered_pull_requests

    async def get_issues(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[Issue]:
        """Fetch issues with our exact same API and business logic."""
        if not repo.include_issues:
            return []

        owner, repo_name = repo.name.split("/")
        query_parts = [
            f"repo:{owner}/{repo_name}",
            "is:issue",
            f"created:>{since.isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        ]

        search_query = " ".join(query_parts)
        variables: dict[str, Any] = {"searchQuery": search_query}

        issues_data = await self._paginate_graphql(
            GET_ISSUES_QUERY,
            variables,
            lambda data: data["search"],
        )

        filtered_issues = []
        for item in issues_data:
            issue_labels = [label["name"] for label in item.get("labels", {}).get("nodes", [])]

            if filters.issues:
                if filters.issues.author and item["author"] and item["author"]["login"] != filters.issues.author:
                    continue
                if filters.issues.labels:
                    if not all(label in issue_labels for label in filters.issues.labels):
                        continue
                if (
                    filters.issues.milestone
                    and item["milestone"]
                    and item["milestone"]["title"] != filters.issues.milestone
                ):
                    continue
                if (
                    filters.issues.assignee
                    and item["assignees"]
                    and not any(assignee["login"] == filters.issues.assignee for assignee in item["assignees"]["nodes"])
                ):
                    continue
                if filters.issues.exclude_issue_titles_regex:
                    if re.search(filters.issues.exclude_issue_titles_regex, item["title"]):
                        continue

            filtered_issues.append(
                Issue(
                    number=item["number"],
                    title=item["title"],
                    body=item["body"],
                    author=item["author"]["login"] if item["author"] else "Unknown",
                    state=item["state"],
                    created_at=item["createdAt"],
                    html_url=item["url"],
                    labels=issue_labels,
                )
            )
        return filtered_issues

    async def get_discussions(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[Discussion]:
        """Fetch discussions with our exact same API and business logic."""
        if not repo.include_discussions:
            return []

        owner, repo_name = repo.name.split("/")
        variables: dict[str, Any] = {"owner": owner, "repo": repo_name}

        discussions_data = await self._paginate_graphql(
            GET_DISCUSSIONS_QUERY,
            variables,
            lambda data: data["repository"]["discussions"],
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

            discussion_labels = [label["name"] for label in item.get("labels", {}).get("nodes", [])]
            filtered_discussions.append(
                Discussion(
                    id=item["id"],
                    title=item["title"],
                    body=item["body"],
                    author=item["author"]["login"] if item["author"] else "Unknown",
                    created_at=item["createdAt"],
                    html_url=item["url"],
                    labels=discussion_labels,
                )
            )
        return filtered_discussions

    async def get_all_labels(self, owner: str, repo_name: str) -> list[str]:
        """Fetch all repository labels."""
        variables: dict[str, Any] = {"owner": owner, "name": repo_name}
        labels_data = await self._paginate_graphql(
            GET_ALL_LABELS_QUERY,
            variables,
            lambda data: data["repository"]["labels"],
        )
        return [label["name"] for label in labels_data]

    async def _paginate_graphql(
        self,
        query: str,
        variables: dict[str, Any],
        data_extractor: Callable[[dict[str, Any]], dict[str, Any]],
        max_pages: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Our same pagination logic, but using gidgethub for HTTP requests.

        Args:
            query: GraphQL query string
            variables: Query variables
            data_extractor: Function to extract data from GraphQL response
            max_pages: Maximum pages to fetch

        Returns:
            List of all nodes from paginated results
        """
        all_nodes = []
        has_next_page = True
        cursor = None
        variables = dict(variables)

        i = 0
        while has_next_page and i < max_pages:
            variables.update({"cursor": cursor})

            logger.debug("Making GraphQL request (page %d): %s", i + 1, query[:100] + "...")

            # Use gidgethub for the request (gets automatic rate limiting, retries, caching)
            try:
                assert self.gh_client is not None, "GitHub client not initialized"
                result = await self.gh_client.graphql(query, **variables)
            except Exception as e:
                logger.error("GraphQL request failed: %s", e)
                raise

            # Log rate limit info if available
            if self.rate_limit:
                logger.debug(
                    "Rate limit: %d/%d remaining, resets at %s",
                    self.rate_limit.remaining,
                    self.rate_limit.limit,
                    self.rate_limit.reset_datetime,
                )

            page_data = data_extractor(result)
            all_nodes.extend(page_data["nodes"])
            has_next_page = page_data["pageInfo"]["hasNextPage"]
            cursor = page_data["pageInfo"]["endCursor"]
            i += 1

        if has_next_page and i >= max_pages:
            logger.warning("Reached maximum page limit (%d). Some data may be missing.", max_pages)

        logger.info("Fetched %d total items across %d pages", len(all_nodes), i)
        return all_nodes
