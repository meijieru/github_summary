import pytest
from unittest.mock import patch
from github_summary.github_client import GitHubService
from github_summary.models import (
    FilterConfig,
    RepoConfig,
    CommitFilterConfig,
    PullRequestFilterConfig,
    IssueFilterConfig,
    DiscussionFilterConfig,
)
from datetime import datetime, timedelta, UTC


@pytest.fixture
def mock_requests():
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        yield mock_get, mock_post


def test_github_service_commits(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {
                                    "oid": "12345",
                                    "messageHeadline": "feat: initial commit",
                                    "author": {
                                        "name": "test_author",
                                        "date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                                    },
                                    "url": "https://github.com/owner/repo/commit/12345",
                                }
                            ],
                        }
                    }
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_commits=True)
    filters = FilterConfig()

    commits = service.get_commits(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(commits) == 1
    assert commits[0].author == "test_author"
    assert commits[0].message == "feat: initial commit"


def test_github_service_commits_exclude_regex(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {
                                    "oid": "1",
                                    "messageHeadline": "feat: new feature",
                                    "author": {
                                        "name": "test_author",
                                        "date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                                    },
                                    "url": "https://github.com/owner/repo/commit/1",
                                },
                                {
                                    "oid": "2",
                                    "messageHeadline": "vim-patch: some patch",
                                    "author": {
                                        "name": "test_author",
                                        "date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                                    },
                                    "url": "https://github.com/owner/repo/commit/2",
                                },
                                {
                                    "oid": "3",
                                    "messageHeadline": "fix: a bug",
                                    "author": {
                                        "name": "test_author",
                                        "date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                                    },
                                    "url": "https://github.com/owner/repo/commit/3",
                                },
                            ],
                        }
                    }
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_commits=True)
    filters = FilterConfig(commits=CommitFilterConfig(exclude_commit_messages_regex="^(vim-patch|fix|doc update)"))

    commits = service.get_commits(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(commits) == 1
    assert commits[0].message == "feat: new feature"


def test_github_service_commits_disabled():
    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_commits=False)
    filters = FilterConfig()
    commits = service.get_commits(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(commits) == 0


def test_github_service_pull_requests(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "number": 101,
                            "title": "Test PR",
                            "body": "Test PR body",
                            "author": {"login": "pr_author"},
                            "state": "CLOSED",
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "mergedAt": "2025-01-02T00:00:00Z",
                            "updatedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/pull/101",
                        }
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_pull_requests=True)
    filters = FilterConfig()

    pull_requests = service.get_pull_requests(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(pull_requests) == 1
    assert pull_requests[0].title == "Test PR"
    assert pull_requests[0].author == "pr_author"
    assert pull_requests[0].body == "Test PR body"


def test_github_service_pull_requests_exclude_regex(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "number": 1,
                            "title": "feat: new feature",
                            "body": "Test body",
                            "author": {"login": "pr_author"},
                            "state": "OPEN",
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "mergedAt": None,
                            "updatedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/pull/1",
                        },
                        {
                            "number": 2,
                            "title": "WIP: work in progress",
                            "body": "Test body",
                            "author": {"login": "pr_author"},
                            "state": "OPEN",
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "mergedAt": None,
                            "updatedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/pull/2",
                        },
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_pull_requests=True)
    filters = FilterConfig(pull_requests=PullRequestFilterConfig(exclude_pull_request_titles_regex="^(WIP|Draft)"))

    pull_requests = service.get_pull_requests(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(pull_requests) == 1
    assert pull_requests[0].title == "feat: new feature"


def test_github_service_pull_requests_disabled():
    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_pull_requests=False)
    filters = FilterConfig()
    pull_requests = service.get_pull_requests(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(pull_requests) == 0


def test_github_service_issues(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "search": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": [
                    {
                        "number": 1,
                        "title": "Test Issue",
                        "body": "Test Issue body",
                        "author": {"login": "test_author"},
                        "state": "OPEN",
                        "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "url": "https://github.com/owner/repo/discussions/2",
                    }
                ],
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_issues=True)
    filters = FilterConfig()
    issues = service.get_issues(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(issues) == 1
    assert issues[0].title == "Test Issue"
    assert issues[0].body == "Test Issue body"


def test_github_service_issues_exclude_regex(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "search": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": [
                    {
                        "number": 1,
                        "title": "feat: new feature",
                        "body": "Test body",
                        "author": {"login": "test_author"},
                        "state": "OPEN",
                        "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "url": "https://github.com/owner/repo/issues/1",
                    },
                    {
                        "number": 2,
                        "title": "Bug: something is broken",
                        "body": "Test body",
                        "author": {"login": "test_author"},
                        "state": "OPEN",
                        "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "url": "https://github.com/owner/repo/issues/2",
                    },
                ],
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_issues=True)
    filters = FilterConfig(issues=IssueFilterConfig(exclude_issue_titles_regex="^(Bug|Question)"))

    issues = service.get_issues(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(issues) == 1
    assert issues[0].title == "feat: new feature"


def test_github_service_issues_filter_tag(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "search": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": [
                    {
                        "number": 1,
                        "title": "Issue with bug tag",
                        "body": "Test body",
                        "author": {"login": "test_author"},
                        "state": "OPEN",
                        "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "labels": {"nodes": [{"name": "bug"}]},
                        "url": "https://github.com/owner/repo/issues/1",
                    }
                ],
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_issues=True)
    filters = FilterConfig(issues=IssueFilterConfig(labels=["bug"]))

    issues = service.get_issues(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(issues) == 1
    assert issues[0].title == "Issue with bug tag"


def test_github_service_pull_requests_filter_state(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "number": 1,
                            "title": "Open PR",
                            "body": "Test body",
                            "author": {"login": "pr_author"},
                            "state": "OPEN",
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "mergedAt": None,
                            "updatedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/pull/1",
                        }
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_pull_requests=True)
    filters = FilterConfig(pull_requests=PullRequestFilterConfig(state="OPEN"))

    pull_requests = service.get_pull_requests(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(pull_requests) == 1
    assert pull_requests[0].title == "Open PR"


def test_github_service_pull_requests_filter_labels(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "number": 1,
                            "title": "PR with bug label",
                            "body": "Test body",
                            "author": {"login": "pr_author"},
                            "state": "OPEN",
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "mergedAt": None,
                            "labels": {"nodes": [{"name": "bug"}]},
                            "updatedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/pull/1",
                        }
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_pull_requests=True)
    filters = FilterConfig(pull_requests=PullRequestFilterConfig(labels=["bug"]))

    pull_requests = service.get_pull_requests(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(pull_requests) == 1
    assert pull_requests[0].title == "PR with bug label"


def test_github_service_issues_filter_assignee(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "search": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": [
                    {
                        "number": 1,
                        "title": "Issue assigned to user1",
                        "body": "Test body",
                        "author": {"login": "test_author"},
                        "state": "OPEN",
                        "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "assignees": {"nodes": [{"login": "user1"}]},
                        "url": "https://github.com/owner/repo/issues/1",
                    }
                ],
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_issues=True)
    filters = FilterConfig(issues=IssueFilterConfig(assignee="user1"))

    issues = service.get_issues(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(issues) == 1
    assert issues[0].title == "Issue assigned to user1"


def test_github_service_issues_disabled():
    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_issues=False)
    filters = FilterConfig()
    issues = service.get_issues(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(issues) == 0


def test_github_service_issues_filter_since_days(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "search": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": [
                    {
                        "number": 1,
                        "title": "Old Issue",
                        "body": "Test body",
                        "author": {"login": "test_author"},
                        "state": "OPEN",
                        "createdAt": (datetime.now(UTC) - timedelta(days=10)).isoformat(),
                        "url": "https://github.com/owner/repo/issues/1",
                    },
                    {
                        "number": 2,
                        "title": "Recent Issue",
                        "body": "Test body",
                        "author": {"login": "test_author"},
                        "state": "OPEN",
                        "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "url": "https://github.com/owner/repo/issues/2",
                    },
                ],
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_issues=True)
    filters = FilterConfig()

    issues = service.get_issues(repo, filters, since=datetime.now(UTC) - timedelta(days=5))
    assert len(issues) == 2
    assert issues[0].title == "Old Issue"
    assert issues[1].title == "Recent Issue"


def test_github_service_discussions(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "discussions": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "D_kwDOJ-L_c84AAQ",
                            "title": "Test Discussion",
                            "body": "Test Discussion body",
                            "author": {"login": "test_author"},
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/discussions/1",
                            "labels": {"nodes": [{"name": "bug"}]},
                        }
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_discussions=True)
    filters = FilterConfig()

    discussions = service.get_discussions(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(discussions) == 1
    assert discussions[0].title == "Test Discussion"
    assert discussions[0].labels == ["bug"]
    assert discussions[0].body == "Test Discussion body"


def test_github_service_discussions_disabled():
    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_discussions=False)
    filters = FilterConfig()
    discussions = service.get_discussions(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(discussions) == 0


def test_github_service_discussions_filter_since_days(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "discussions": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "D_kwDOJ-L_c84AAQ",
                            "title": "Old Discussion",
                            "body": "Test body",
                            "author": {"login": "test_author"},
                            "createdAt": (datetime.now(UTC) - timedelta(days=10)).isoformat(),
                            "url": "https://github.com/owner/repo/discussions/1",
                        },
                        {
                            "id": "D_kwDOJ-L_c84AAQ",
                            "title": "Recent Discussion",
                            "body": "Test body",
                            "author": {"login": "test_author"},
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/discussions/2",
                        },
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_discussions=True)
    filters = FilterConfig()

    discussions = service.get_discussions(repo, filters, since=datetime.now(UTC) - timedelta(days=5))
    assert len(discussions) == 1
    assert discussions[0].title == "Recent Discussion"


def test_github_service_discussions_filter_author(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "discussions": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "D_kwDOJ-L_c84AAQ",
                            "title": "Discussion by Author1",
                            "body": "Test body",
                            "author": {"login": "author1"},
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/discussions/1",
                        },
                        {
                            "id": "D_kwDOJ-L_c84AAQ",
                            "title": "Discussion by Author2",
                            "body": "Test body",
                            "author": {"login": "author2"},
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/discussions/2",
                        },
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_discussions=True)
    filters = FilterConfig(discussions=DiscussionFilterConfig(author="author1"))

    discussions = service.get_discussions(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(discussions) == 1
    assert discussions[0].title == "Discussion by Author1"


def test_github_service_discussions_exclude_regex(mock_requests):
    _, mock_post = mock_requests
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "discussions": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "D_kwDOJ-L_c84AAQ",
                            "title": "General Discussion",
                            "body": "Test body",
                            "author": {"login": "test_author"},
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/discussions/1",
                        },
                        {
                            "id": "D_kwDOJ-L_c84AAQ",
                            "title": "Question: How to do X?",
                            "body": "Test body",
                            "author": {"login": "test_author"},
                            "createdAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/discussions/2",
                        },
                    ],
                }
            }
        }
    }

    service = GitHubService(token="test_token")
    repo = RepoConfig(name="owner/repo", include_discussions=True)
    filters = FilterConfig(discussions=DiscussionFilterConfig(exclude_discussion_titles_regex="^(Question)"))

    discussions = service.get_discussions(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(discussions) == 1
    assert discussions[0].title == "General Discussion"
