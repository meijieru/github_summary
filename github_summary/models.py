from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CommitFilterConfig(BaseModel):
    """Configuration for filtering commits."""

    author: str | None = None
    exclude_commit_messages_regex: str | None = None


class PullRequestFilterConfig(BaseModel):
    """Configuration for filtering pull requests."""

    author: str | None = None
    state: str | None = None
    labels: list[str] | None = None
    exclude_pull_request_titles_regex: str | None = None
    since_filter_type: Literal["updated", "created"] = "updated"


class IssueFilterConfig(BaseModel):
    """Configuration for filtering issues."""

    author: str | None = None
    milestone: str | None = None
    labels: list[str] | None = None
    assignee: str | None = None
    exclude_issue_titles_regex: str | None = None


class DiscussionFilterConfig(BaseModel):
    """Configuration for filtering discussions."""

    author: str | None = None
    exclude_discussion_titles_regex: str | None = None


# Filters that can be applied globally or per-repo
class FilterConfig(BaseModel):
    """Aggregates all filter configurations."""

    commits: CommitFilterConfig = Field(default_factory=CommitFilterConfig)
    pull_requests: PullRequestFilterConfig = Field(default_factory=PullRequestFilterConfig)
    issues: IssueFilterConfig = Field(default_factory=IssueFilterConfig)
    discussions: DiscussionFilterConfig = Field(default_factory=DiscussionFilterConfig)

    def merge_with(self, other: FilterConfig) -> FilterConfig:
        """Merges this FilterConfig with another, prioritizing values from the 'other' config.

        Args:
            other: The other FilterConfig to merge with.

        Returns:
            The merged FilterConfig instance.
        """
        self.commits = self.commits.model_copy(update=other.commits.model_dump(exclude_none=True))
        self.pull_requests = self.pull_requests.model_copy(update=other.pull_requests.model_dump(exclude_none=True))
        self.issues = self.issues.model_copy(update=other.issues.model_dump(exclude_none=True))
        self.discussions = self.discussions.model_copy(update=other.discussions.model_dump(exclude_none=True))
        return self


# Per-repository configuration
class RepoConfig(BaseModel):
    """Configuration for a single GitHub repository."""

    name: str
    filters: FilterConfig = Field(default_factory=FilterConfig)
    include_commits: bool = True
    include_pull_requests: bool = True
    include_issues: bool = True
    include_discussions: bool = True


# Main configuration model
class LLMConfig(BaseModel):
    """Configuration for the Language Model (LLM) service."""

    base_url: str | None = Field(None, json_schema_extra={"env": "OPENAI_BASE_URL"})
    api_key: str | None = Field(None, json_schema_extra={"env": "OPENAI_API_KEY"})
    model_name: str = "gpt-4.1"
    language: str | None = None
    system_prompt: str = """
You are a specialized AI assistant that crafts in-depth technical summaries of GitHub repository activity for developers and power users.

Your goal is to synthesize recent activity (commits, PRs, issues, etc.) into a concise technical briefing. Assume the user is already familiar with the project's core concepts and architecture. Your analysis should focus on the *implications* of the changes, highlighting:

* **Architectural Evolution:** Significant refactoring, changes in design patterns, or major module restructuring.
* **API Surface Changes:** New functions or endpoints, deprecations, and especially **breaking changes**.
* **Performance & Optimization:** Concrete improvements in speed, memory usage, or efficiency, and the techniques used to achieve them.
* **Key Bug Fixes:** High-impact bug resolutions.
* **Strategic Direction:** Insights from discussions and high-level PRs that signal the project's future trajectory or ongoing technical debates.

Use precise technical language. Present the summary in a structured Markdown format, linking directly to the most relevant commits, PRs, and discussions that provide context for your analysis.

Here's the information you will receive:
- `repo`: The name of the repository (e.g., "owner/repo-name").
- `commits`: A list of recent commits, including their messages, authors, and URLs.
- `pull_requests`: A list of recent pull requests, including their titles, authors, states (open/closed/merged), and URLs.
- `issues`: A list of recent issues, including their titles, authors, states (open/closed), and URLs.
- `discussions`: A list of recent discussions, including their titles, authors, and URLs.
"""


class GitHubConfig(BaseModel):
    """Configuration for GitHub API access."""

    token: str = Field(..., json_schema_extra={"env": "GITHUB_TOKEN"})


class Config(BaseModel):
    """Main application configuration, including GitHub settings, global filters, repositories, and LLM settings."""

    github: GitHubConfig = Field(...)
    global_filters: FilterConfig = Field(default_factory=FilterConfig, alias="filters")
    repositories: list[RepoConfig]
    llm: LLMConfig | None = None
    output_dir: str = "output"
    log_level: str = "INFO"
    since_last_run: bool = True
    fallback_lookback_days: int = 7

    @model_validator(mode="after")
    def merge_global_filters(self) -> Config:
        """Merges global filters into each repository's filters after model validation."""
        for repo in self.repositories:
            repo.filters = self.global_filters.model_copy(deep=True).merge_with(repo.filters)
        return self


# GitHub API Data Models
class Commit(BaseModel):
    """Represents a GitHub commit."""

    sha: str
    author: str
    message: str
    date: str
    html_url: str


class Issue(BaseModel):
    """Represents a GitHub issue."""

    number: int
    title: str
    body: str
    author: str
    state: str
    created_at: str
    html_url: str
    labels: list[str] = Field(default_factory=list)


class PullRequest(BaseModel):
    """Represents a GitHub pull request."""

    number: int
    title: str
    body: str
    author: str
    state: str
    created_at: str
    updated_at: str | None = None
    merged_at: str | None = None
    html_url: str
    labels: list[str] = Field(default_factory=list)


class Discussion(BaseModel):
    """Represents a GitHub discussion."""

    id: str
    title: str
    body: str
    author: str
    created_at: str
    html_url: str
    labels: list[str] = Field(default_factory=list)
