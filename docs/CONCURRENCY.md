# Concurrency Control in GitHub Summary

This document explains how the two-level concurrency control system works in the GitHub Summary tool.

## Overview

The tool uses a **two-tier concurrency control system** to optimize performance while respecting API rate limits:

1. **Repository-level concurrency**: Controls how many repositories are processed simultaneously
2. **LLM-level concurrency**: Controls how many LLM API requests can be made simultaneously

## How They Interact

### Repository Concurrency (Outer Level)
- **Purpose**: Limits how many repositories are processed at the same time
- **Default**: 4 repositories
- **Configuration**: `max_concurrent_repos` in config.toml
- **Scope**: Each repository involves fetching GitHub data + generating LLM summary

### LLM Concurrency (Inner Level)  
- **Purpose**: Limits concurrent LLM API requests across all repositories
- **Default**: 3 requests
- **Configuration**: `llm.max_concurrent` in config.toml
- **Scope**: Only applies to LLM API calls, shared across all active repositories

## Multiplication vs Max Control

**These settings work as independent limits, NOT multiplicative:**

```
Total possible concurrent LLM requests = min(active_repositories, llm.max_concurrent)
```

### Example Scenarios:

**Scenario 1: High repository, low LLM concurrency**
- `max_concurrent_repos = 8`
- `llm.max_concurrent = 2`
- **Result**: Up to 8 repositories processed, but only 2 LLM requests at a time

**Scenario 2: Low repository, high LLM concurrency**
- `max_concurrent_repos = 2` 
- `llm.max_concurrent = 10`
- **Result**: Only 2 repositories processed, max 2 LLM requests (limited by active repos)

**Scenario 3: Balanced**
- `max_concurrent_repos = 4`
- `llm.max_concurrent = 3`
- **Result**: Up to 4 repositories processed, max 3 concurrent LLM requests

## Configuration Options

### 1. Configuration File (config.toml)
```toml
[performance]
max_concurrent_repos = 4  # Repository concurrency
max_concurrent_llm = 3    # LLM API concurrency
```

### 2. Environment Variables
```bash
export GHSUM_CONCURRENT_REPOS=6  # Overrides config
```

### 3. CLI Arguments
```bash
github-summary summarize --max-concurrent-repos 8
```

**Priority order**: CLI argument > Environment variable > Config file

## Performance Tuning Guidelines

### Repository Concurrency
- **Start with**: 4 repositories
- **Increase if**: You have many repositories and good network/API limits
- **Decrease if**: Hitting GitHub rate limits or memory constraints
- **Memory impact**: ~10MB per concurrent repository

### LLM Concurrency
- **Start with**: 3 requests  
- **Increase if**: Using high-performance LLM endpoints
- **Decrease if**: Hitting LLM rate limits or getting timeouts
- **API impact**: Directly affects LLM provider rate limits

### Recommended Combinations

| Use Case | Repos | LLM | Reasoning |
|----------|-------|-----|-----------|
| Development/Testing | 2 | 1 | Conservative, avoid rate limits |
| Small teams | 4 | 3 | Balanced performance |
| Large organizations | 6-8 | 3-5 | High throughput with control |
| CI/CD pipelines | 3 | 2 | Stable, predictable performance |

## Monitoring and Troubleshooting

### Log Messages
```
INFO - Starting report generation with max 4 concurrent repositories
INFO - Final rate limit: 4950/5000 remaining
```

### Common Issues

**GitHub Rate Limiting**
- Symptom: "rate limit" errors in logs
- Solution: Reduce `max_concurrent_repos`

**LLM Rate Limiting** 
- Symptom: 429 errors from LLM provider
- Solution: Reduce `llm.max_concurrent`

**Memory Issues**
- Symptom: High memory usage, slow performance
- Solution: Reduce `max_concurrent_repos`

**Slow Performance**
- Symptom: Long processing times
- Solution: Increase concurrency values gradually while monitoring rate limits

## Best Practices

1. **Start Conservative**: Begin with default values and increase gradually
2. **Monitor Rate Limits**: Watch logs for rate limit warnings
3. **Test Changes**: Use `--repo owner/single-repo` to test settings
4. **Environment-Specific**: Use different settings for dev/staging/prod
5. **Document Changes**: Record what works for your specific setup

The key insight is that these are **independent throttles** working together, not multiplying factors. The LLM concurrency acts as a shared resource pool across all active repository processing tasks.
