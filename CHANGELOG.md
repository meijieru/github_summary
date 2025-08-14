# Changelog

## [2.0.0](https://github.com/meijieru/github_summary/compare/v1.0.0...v2.0.0) (2025-08-14)


### ⚠ BREAKING CHANGES

* **app:** unify async core into GitHubSummaryApp, modernize CLI, and update docs/tests

### Features

* **github_client:** add data_type and repo_name to GraphQL fetch for improved logging ([5788cf0](https://github.com/meijieru/github_summary/commit/5788cf02fcf00b4f52aa4b8553a278712be88a01))


### Bug Fixes

* **rss:** add summary cache and refactor RSS feed generation ([f385100](https://github.com/meijieru/github_summary/commit/f3851005b979f90a9548649aefcb5d3ecbc1b399))


### Code Refactoring

* **app:** unify async core into GitHubSummaryApp, modernize CLI, and update docs/tests ([4543870](https://github.com/meijieru/github_summary/commit/4543870016cd92104c330a5e2ca62bdde493ed2e))

## [1.0.0](https://github.com/meijieru/github_summary/compare/v0.2.0...v1.0.0) (2025-08-13)


### ⚠ BREAKING CHANGES

* **scheduler:** use cron scheduler with per-repository support

### Features

* **async:** migrate to async-first architecture, add two-level concurrency control, update docs and tests ([bd1ecdd](https://github.com/meijieru/github_summary/commit/bd1ecdd0fa4a77f4c014aee325b0ddd775a63491))
* **scheduler:** support per-repository schedules and selective report generation ([e1bcf45](https://github.com/meijieru/github_summary/commit/e1bcf455fd57b2ecffc7df605ea403e5a5083b95))
* **scheduler:** use cron scheduler with per-repository support ([a13f269](https://github.com/meijieru/github_summary/commit/a13f269698ae553840b7b30684425b7858d20e03))


### Bug Fixes

* **last_run_manager:** per-repository last run time tracking and retrieval ([59194c0](https://github.com/meijieru/github_summary/commit/59194c05fa4227b0762d0c6d3dbd3e7ef5e9dbba))
* **web:** fix config file priority, support --config in web CLI, and improve reload mode ([004bc6b](https://github.com/meijieru/github_summary/commit/004bc6bf3284f22c85ff187cf4d1c59705443e9b))


### Documentation

* restructure documentation and examples ([5155750](https://github.com/meijieru/github_summary/commit/51557506f0918ff969fcdb2ccb0c190f4eae0125))
* **test:** add pytest-based testing guide, update documentation, and mark tests with pytest markers ([c962545](https://github.com/meijieru/github_summary/commit/c962545fbb39b6bf867d41d0f1ccb7e677bbfadf))

## [0.2.0](https://github.com/meijieru/github_summary/compare/v0.1.1...v0.2.0) (2025-08-11)


### Features

* **web:** add unified web service with scheduler and static file serving ([d3af3f3](https://github.com/meijieru/github_summary/commit/d3af3f3c3471f34cd6118c640d1a63eee7213049))

## [0.1.1](https://github.com/meijieru/github_summary/compare/v0.1.0...v0.1.1) (2025-08-10)


### Bug Fixes

* **project:** add missing tzlocal&gt;=5.3.1 to dependencies in pyproject.toml ([71e8e37](https://github.com/meijieru/github_summary/commit/71e8e37eeb76f061eecf85578fa2dd368d468a16))

## 0.1.0 (2025-08-10)

- Initial release.
