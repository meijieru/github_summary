# Changelog

## 1.0.0 (2025-08-03)


### ⚠ BREAKING CHANGES

* refactor time filtering to use UTC datetime, remove since_days from filters

### Features

* add --save-markdown option to save LLM summary as Markdown file ([6c15226](https://github.com/meijieru/github_summary/commit/6c152266c4fbcaab8114db6086747ca97f4afb85))
* add logging throughout codebase and support configurable log level ([e045c7a](https://github.com/meijieru/github_summary/commit/e045c7a445515399d0dd6dc9791061e333865747))
* **config:** enable commits and discussions by default, expand LLM system prompt for technical summaries ([46f4b6c](https://github.com/meijieru/github_summary/commit/46f4b6ce81fe721089e38ac3ce643592fe1b590e))
* **docker:** add Dockerfile, entrypoint script, and .dockerignore for containerization ([cf6eef5](https://github.com/meijieru/github_summary/commit/cf6eef5690b9583a1e7604517aa1e1be39d8deb7))
* **github:** add body field to PR, issue, and discussion models and queries ([3a81ef4](https://github.com/meijieru/github_summary/commit/3a81ef4d33c324ea450c8983c39a4613138beafb))
* **github:** add since_filter_type for PRs and support filtering by updatedAt ([2d9ceb1](https://github.com/meijieru/github_summary/commit/2d9ceb143615d2623d57545fba811b136f1680d2))
* **github:** include discussion labels in API, model, and tests ([8c0b995](https://github.com/meijieru/github_summary/commit/8c0b9953112b091670faac08299050d464120a2a))
* init commit ([9ce0c75](https://github.com/meijieru/github_summary/commit/9ce0c753717e0a0efd68e6815ff47d714e4cd2fc))
* **llm:** add configurable retries and retry_delay with tenacity for LLM requests ([f2ec2da](https://github.com/meijieru/github_summary/commit/f2ec2da06b2882acdeb11e061d29e816390cbabb))
* refactor time filtering to use UTC datetime, remove since_days from filters ([f19608d](https://github.com/meijieru/github_summary/commit/f19608d201dd39c5ad8f8928ed6f88801e9fd29e))
* **rss:** add RSS feed generation and scheduling support ([1a19f15](https://github.com/meijieru/github_summary/commit/1a19f156d736f84f1881a22807ed4f42eca70a31))
* **rss:** render markdown summaries as HTML in RSS feed entries ([1603474](https://github.com/meijieru/github_summary/commit/1603474449f8f8100b7fc59efb16dd781ecaa1f4))
* **summarizer:** add language option to LLMConfig and Summarizer for multilingual summaries ([87a710d](https://github.com/meijieru/github_summary/commit/87a710dedcdafda4396c52c161712a012f368ad6))
* **summarizer:** add last run time in LLM summary prompt and revise system prompt ([ec2a8a5](https://github.com/meijieru/github_summary/commit/ec2a8a577c9c7a27c85c9b70669803da2ef0a560))
* **summarizer:** add timezone support for summary timestamps and config ([fd06077](https://github.com/meijieru/github_summary/commit/fd060773fe22e8702fe556c1013280d9cd46dd18))


### Bug Fixes

* **actions:** use MY_RELEASE_PLEASE_TOKEN for release-please authentication ([d758ecc](https://github.com/meijieru/github_summary/commit/d758eccb21a1a9641e86faf7ba5354c7460eaf88))
* **github:** not implemented pull request and issue filtering options ([315f7e6](https://github.com/meijieru/github_summary/commit/315f7e61d851c701cf7b9adc81c9052e8d1f2416))
* **github:** remove unsupported author and path filters from GET_COMMITS_QUERY ([850ff54](https://github.com/meijieru/github_summary/commit/850ff54c665befe0fbf28df0bcde4d9b4d466064))
* improve config validation and LLM summary handling ([2b62ab6](https://github.com/meijieru/github_summary/commit/2b62ab641c1401245df5ead08adcc150c4edd61f))
* limit GraphQL pagination to 5 pages to prevent too much loops ([90da88a](https://github.com/meijieru/github_summary/commit/90da88aa81913c83d8f0486ac6845a4012227bbd))
* **llm:** handle missing or malformed LLM response gracefully in summary parsing ([58c9251](https://github.com/meijieru/github_summary/commit/58c9251337811c219eb87d8f696db56fb25f36e7))
* missing --since-days option to summarize command ([d275932](https://github.com/meijieru/github_summary/commit/d275932d39655288db10b5254dba9409c26317e8))
* **summarizer:** strip markdown code fences from LLM summary output ([abf5fc2](https://github.com/meijieru/github_summary/commit/abf5fc2b4a76316c92ce063d6cece24110d24856))
