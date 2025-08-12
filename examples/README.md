# Configuration Examples

This directory contains example configuration files for different use cases.

## Available Examples

### 📁 `basic.toml`

**Simple getting started configuration**

- Minimal setup with one repository
- No scheduling or advanced features
- Perfect for first-time users

### 📁 `minimal.toml`

**Minimal working configuration**

- Basic GitHub and LLM settings
- Template for manual customization
- Good starting point for simple setups

### 📁 `scheduling.toml`

**Comprehensive scheduling examples**

- Multiple cron expression patterns
- Global and per-repository schedules
- Timezone configurations
- Reference for all scheduling options

### 📁 `advanced.toml`

**Full-featured configuration**

- All available options demonstrated
- Complex filtering rules
- RSS feed generation
- Multiple repositories with different settings

## Quick Start

1. Copy one of the example files:

   ```bash
   cp examples/basic.toml config.toml
   ```

2. Edit the configuration:

   - Replace `your_github_token_here` with your GitHub token
   - Replace `your_openai_api_key` with your OpenAI API key
   - Update repository names to match your repositories

3. Run the tool:
   ```bash
   github-summary
   ```

## Configuration Tips

### Scheduling

- Include `[schedule]` section to enable automatic runs
- Omit `[schedule]` section for manual-only operation
- Use per-repository schedules to override global schedule

### Common Cron Patterns

- `"0 9 * * 1"` - Every Monday at 9 AM
- `"0 6,18 * * *"` - Daily at 6 AM and 6 PM
- `"0 9-17 * * 1-5"` - Business hours, weekdays only
- `"*/15 * * * *"` - Every 15 minutes (testing only)

### Filters

- Use regex patterns to exclude irrelevant commits/PRs
- Apply globally or per-repository
- Common pattern: `"^(docs|test|chore|ci):"`

For more details, see the main README.md file.
