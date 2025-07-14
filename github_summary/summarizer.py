from typing import Protocol
import logging

from github_summary.models import Commit, Discussion, Issue, PullRequest

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """A protocol defining the interface for an LLM client.

    Any class implementing this protocol must provide a `generate_summary` method.
    """

    def generate_summary(self, prompt: str) -> str: ...


class Summarizer:
    def __init__(self, llm_client: LLMClient, system_prompt: str):
        """Initializes the Summarizer with an LLM client and a system prompt.

        Args:
            llm_client: An instance of a class implementing the LLMClient protocol.
            system_prompt: The base system prompt to use for summarization.
        """
        logger.info("Initializing Summarizer.")
        self.llm_client = llm_client
        self.system_prompt = system_prompt

    def summarize(
        self,
        commits: list[Commit],
        pull_requests: list[PullRequest],
        issues: list[Issue],
        discussions: list[Discussion],
    ) -> str:
        """Generates a summary of GitHub activity using the LLM client.

        Args:
            commits: A list of Commit objects.
            pull_requests: A list of PullRequest objects.
            issues: A list of Issue objects.
            discussions: A list of Discussion objects.

        Returns:
            A string containing the generated summary.
        """
        if not commits and not pull_requests and not issues and not discussions:
            logger.info("No new updates found.")
            return "No new updates."

        logger.info("Generating LLM prompt.")
        prompt = self._generate_llm_prompt(commits, pull_requests, issues, discussions)
        logger.debug("Generated prompt length: %d", len(prompt))
        return self.llm_client.generate_summary(prompt)

    def _generate_llm_prompt(
        self,
        commits: list[Commit],
        pull_requests: list[PullRequest],
        issues: list[Issue],
        discussions: list[Discussion],
    ) -> str:
        """Generates a formatted prompt string for the LLM based on the provided GitHub activity data.

        Args:
            commits: A list of Commit objects.
            pull_requests: A list of PullRequest objects.
            issues: A list of Issue objects.
            discussions: A list of Discussion objects.

        Returns:
            A string formatted as a prompt for the LLM.
        """
        prompt = f"{self.system_prompt}\n\n"

        if commits:
            logger.debug("Adding commits to prompt.")
            prompt += "Commits:\n"
            for commit in commits:
                prompt += f"- [{commit.author}: {commit.message}]({commit.html_url}) ({commit.date})\n"

        if pull_requests:
            logger.debug("Adding pull requests to prompt.")
            prompt += "\nPull Requests:\n"
            for pr in pull_requests:
                prompt += f"- [#{pr.number}: {pr.title}]({pr.html_url}) ({pr.state}) by {pr.author}\n"

        if issues:
            logger.debug("Adding issues to prompt.")
            prompt += "\nIssues:\n"
            for issue in issues:
                prompt += f"- [#{issue.number}: {issue.title}]({issue.html_url}) ({issue.state}) by {issue.author} ({issue.created_at})\n"

        if discussions:
            logger.debug("Adding discussions to prompt.")
            prompt += "\nDiscussions:\n"
            for discussion in discussions:
                prompt += (
                    f"- [{discussion.title}]({discussion.html_url}) by {discussion.author} ({discussion.created_at})\n"
                )

        return prompt
