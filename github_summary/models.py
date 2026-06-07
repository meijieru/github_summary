from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from tzlocal import get_localzone_name

from github_summary.paths import get_default_run_dir


class StrictConfigModel(BaseModel):
    """Base model for user configuration sections."""

    model_config = ConfigDict(extra="forbid")


class CommitFilterConfig(StrictConfigModel):
    """Configuration for filtering commits."""

    author: str | None = None
    exclude_commit_messages_regex: str | None = None


class PullRequestFilterConfig(StrictConfigModel):
    """Configuration for filtering pull requests."""

    author: str | None = None
    state: str | None = None
    labels: list[str] | None = None
    exclude_pull_request_titles_regex: str | None = None
    since_filter_type: Literal["updated", "created"] = "updated"


class IssueFilterConfig(StrictConfigModel):
    """Configuration for filtering issues."""

    author: str | None = None
    milestone: str | None = None
    labels: list[str] | None = None
    assignee: str | None = None
    exclude_issue_titles_regex: str | None = None


class DiscussionFilterConfig(StrictConfigModel):
    """Configuration for filtering discussions."""

    author: str | None = None
    exclude_discussion_titles_regex: str | None = None


class ReleaseFilterConfig(StrictConfigModel):
    """Configuration for filtering releases."""

    author: str | None = None
    exclude_release_names_regex: str | None = None
    exclude_prereleases: bool = True


# Filters that can be applied globally or per-repo
class FilterConfig(StrictConfigModel):
    """Aggregates all filter configurations."""

    commits: CommitFilterConfig = Field(default_factory=CommitFilterConfig)
    pull_requests: PullRequestFilterConfig = Field(default_factory=PullRequestFilterConfig)
    issues: IssueFilterConfig = Field(default_factory=IssueFilterConfig)
    discussions: DiscussionFilterConfig = Field(default_factory=DiscussionFilterConfig)
    releases: ReleaseFilterConfig = Field(default_factory=ReleaseFilterConfig)

    def merge_with(self, other: Self) -> Self:
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
        self.releases = self.releases.model_copy(update=other.releases.model_dump(exclude_none=True))
        return self


class ScheduleConfig(StrictConfigModel):
    """Configuration for scheduling the summarization using cron syntax."""

    cron: str = "0 6 * * *"  # Default: daily at 6 AM (cron format: minute hour day month weekday)
    timezone: str | None = None  # Optional timezone (e.g., "America/New_York", "UTC")


# Per-repository configuration
class RepoConfig(StrictConfigModel):
    """Configuration for a single GitHub repository."""

    name: str
    audience: Literal["user", "maintainer", "mixed"] | None = None
    filters: FilterConfig = Field(default_factory=FilterConfig)
    include_commits: bool = True
    include_pull_requests: bool = True
    include_issues: bool = True
    include_discussions: bool = True
    include_releases: bool = False
    release_only: bool = False
    schedule: ScheduleConfig | None = None

    @model_validator(mode="after")
    def validate_release_only(self) -> Self:
        """Ensures that if release_only is True, all other include flags are False."""
        if self.release_only:
            self.include_commits = False
            self.include_pull_requests = False
            self.include_issues = False
            self.include_discussions = False
            self.include_releases = True
        return self


# Main configuration model
class LLMConfig(StrictConfigModel):
    """Configuration for the Language Model (LLM) service."""

    base_url: str | None = Field(None, json_schema_extra={"env": "OPENAI_BASE_URL"})
    api_key: str | None = Field(None, json_schema_extra={"env": "OPENAI_API_KEY"})
    model_name: str = "gpt-4.1"
    language: str | None = None
    audience: Literal["user", "maintainer", "mixed"] = "mixed"
    retries: int = 3
    retry_exp_multiplier: int = 1
    system_prompt: str = """
You generate concise, high-signal GitHub activity summaries for technically literate readers.
Prefer factual, evidence-based wording over promotional release-note language.
"""


class GitHubConfig(StrictConfigModel):
    """Configuration for GitHub API access."""

    token: str = Field(..., json_schema_extra={"env": "GITHUB_TOKEN"})


class RssConfig(StrictConfigModel):
    """Configuration for the RSS feed."""

    title: str = "GitHub Repository Summaries"
    link: str = "http://localhost/rss.xml"
    description: str = "Summaries of recent activity in GitHub repositories."
    filename: str = "rss.xml"


class PerformanceConfig(StrictConfigModel):
    """Configuration for performance and concurrency settings."""

    max_concurrent_repos: int = Field(4, description="Maximum number of repositories to process concurrently")
    max_concurrent_llm: int = Field(3, description="Maximum number of concurrent LLM API requests")


class Config(StrictConfigModel):
    """Main application configuration, including GitHub settings, global filters, repositories, and LLM settings."""

    github: GitHubConfig = Field(...)
    global_filters: FilterConfig = Field(default_factory=FilterConfig, alias="filters")
    repositories: list[RepoConfig]
    llm: LLMConfig | None = None
    rss: RssConfig | None = None
    schedule: ScheduleConfig | None = None
    performance: PerformanceConfig = Field(
        default_factory=lambda: PerformanceConfig(max_concurrent_repos=4, max_concurrent_llm=3)
    )
    run_dir: str = Field(default_factory=get_default_run_dir)
    output_dir: str = "output"
    cache_dir: str = "cache"
    log_dir: str = "log"
    log_level: str = "INFO"
    since_last_run: bool = True
    fallback_lookback_days: int = 7
    timezone: str = Field(default_factory=get_localzone_name)

    @model_validator(mode="after")
    def merge_global_filters(self) -> Self:
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


class Release(BaseModel):
    """Represents a GitHub release."""

    id: str
    name: str
    tag_name: str
    body: str
    author: str
    created_at: str
    html_url: str
    is_prerelease: bool
