from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator
from tzlocal import get_localzone_name


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
    schedule: ScheduleConfig | None = None


# Main configuration model
class LLMConfig(BaseModel):
    """Configuration for the Language Model (LLM) service."""

    base_url: str | None = Field(None, json_schema_extra={"env": "OPENAI_BASE_URL"})
    api_key: str | None = Field(None, json_schema_extra={"env": "OPENAI_API_KEY"})
    model_name: str = "gpt-4.1"
    language: str | None = None
    retries: int = 3
    retry_delay: int = 1
    system_prompt: str = """
You are a specialized AI assistant that crafts high-level technical changelogs from GitHub repository activity. Your audience is experienced developers and project maintainers who are already familiar with the project's core architecture.

Your goal is to generate a two-part summary: a detailed analysis of completed work and a brief overview of ongoing developments.

### **Part 1: In-Depth Technical Summary**

Analyze recent **merged** pull requests, **closed** issues, and direct **commits** to create a concise, impact-focused briefing. Your analysis must prioritize the following topics in order:

* **✨ New Features & Capabilities:** Detail significant, user-facing additions or major new functionalities. Explain *what* the new feature is and its intended benefit.
* **🐛 Critical Bug Fixes:** Focus only on fixes for high-impact bugs, such as those causing crashes, data corruption, security vulnerabilities, or significant functional failures. Describe the problem that was solved.
* **⚠️ Breaking Changes & Deprecations:** Explicitly call out any changes to the API, configuration, or behavior that are not backward-compatible. List any functions, endpoints, or features that have been deprecated.
* **🏗️ Major Architectural & Performance Improvements:** Describe significant code refactoring, changes to design patterns, or concrete optimizations that yield measurable gains in performance or resource usage.
* **🧭 Strategic Direction:** Synthesize insights from `discussions` and high-level PR comments that signal the project's future trajectory or key technical debates.

### **Part 2: Ongoing Developments**

After the main summary, add a separate section titled "👀 Active Developments" to provide a quick glance at work in progress.

* In this section, list recently **updated but still open** pull requests.
* For each PR, provide its title, a link, and a **concise 1-2 sentence summary** of its primary goal, based on its title and description.
* This section is for a high-level overview only; do not perform a deep analysis of the code changes.

---

### **Important Instructions**

* **Focus on Impact:** For Part 1, do not simply list changes. Explain the *implication* of the work.
* **Be Selective:** You **must ignore** minor changes in your main summary. This includes:
    * Minor bug fixes (e.g., typos, UI styling tweaks).
    * Routine maintenance (e.g., dependency updates, CI/CD tweaks).
    * Documentation-only updates.

Present the final output in a structured Markdown format, linking directly to the relevant PRs, commits, or discussions.

---

### **Input Data**

You will receive the following information:
* `repo`: The name of the repository (e.g., "owner/repo-name").
* `commits`: A list of recent commits, including those made directly to the main branch.
* `pull_requests`: A list of recent pull requests, including their titles, authors, states (open/closed/merged), and URLs. Use this for both Part 1 (merged) and Part 2 (open).
* `issues`: A list of recent issues, including their titles, authors, states (open/closed), and URLs.
* `discussions`: A list of recent discussions to inform the "Strategic Direction" analysis.
"""


class GitHubConfig(BaseModel):
    """Configuration for GitHub API access."""

    token: str = Field(..., json_schema_extra={"env": "GITHUB_TOKEN"})


class RssConfig(BaseModel):
    """Configuration for the RSS feed."""

    enabled: bool = False
    title: str = "GitHub Repository Summaries"
    link: str = "http://localhost/rss.xml"
    description: str = "Summaries of recent activity in GitHub repositories."
    filename: str = "rss.xml"


class ScheduleConfig(BaseModel):
    """Configuration for scheduling the summarization."""

    enabled: bool = False
    run_at: list[str] = Field(default_factory=lambda: ["06:00"])  # in HH:MM format


class Config(BaseModel):
    """Main application configuration, including GitHub settings, global filters, repositories, and LLM settings."""

    github: GitHubConfig = Field(...)
    global_filters: FilterConfig = Field(default_factory=FilterConfig, alias="filters")
    repositories: list[RepoConfig]
    llm: LLMConfig | None = None
    rss: RssConfig | None = None
    schedule: ScheduleConfig | None = None
    output_dir: str = "output"
    log_level: str = "INFO"
    since_last_run: bool = True
    fallback_lookback_days: int = 7
    timezone: str = Field(default_factory=get_localzone_name)

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
