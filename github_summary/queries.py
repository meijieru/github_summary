"""
This module contains all GraphQL queries used in the application.
"""

# Note: fragments are not used because they are not supported by the current version of the graphql client.

GET_COMMITS_QUERY = """
query($owner: String!, $repo: String!, $since: GitTimestamp, $until: GitTimestamp, $cursor: String) {
    repository(owner: $owner, name: $repo) {
        defaultBranchRef {
            target {
                ... on Commit {
                    history(first: 100, after: $cursor, since: $since, until: $until) {
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                        nodes {
                            oid
                            messageHeadline
                            author {
                                name
                                date
                            }
                            url
                        }
                    }
                }
            }
        }
    }
}
"""

GET_PULL_REQUESTS_QUERY = """
query($owner: String!, $repo: String!, $state: [PullRequestState!], $labels: [String!], $cursor: String) {
    repository(owner: $owner, name: $repo) {
        pullRequests(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}, states: $state, labels: $labels) {
            pageInfo {
                endCursor
                hasNextPage
            }
            nodes {
                number
                title
                body
                author {
                    login
                }
                state
                createdAt
                mergedAt
                updatedAt
                url
                labels(first: 10) {
                    nodes {
                        name
                    }
                }
            }
        }
    }
}
"""

GET_ISSUES_QUERY = """
query($searchQuery: String!, $cursor: String) {
    search(query: $searchQuery, type: ISSUE, first: 100, after: $cursor) {
        pageInfo {
            endCursor
            hasNextPage
        }
        nodes {
            ... on Issue {
                number
                title
                body
                author {
                    login
                }
                state
                createdAt
                url
                labels(first: 10) {
                    nodes {
                        name
                    }
                }
            }
        }
    }
}
"""

GET_DISCUSSIONS_QUERY = """
query($owner: String!, $repo: String!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
        discussions(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
            pageInfo {
                endCursor
                hasNextPage
            }
            nodes {
                id
                title
                body
                author {
                    login
                }
                createdAt
                url
                labels(first: 10) {
                    nodes {
                        name
                    }
                }
            }
        }
    }
}
"""

GET_ALL_LABELS_QUERY = """
query GetRepositoryLabels($owner: String!, $name: String!, $cursor: String) {
    repository(owner: $owner, name: $name) {
        labels(first: 100, after: $cursor) {
            pageInfo {
                endCursor
                hasNextPage
            }
            nodes {
                name
            }
        }
    }
}
"""
