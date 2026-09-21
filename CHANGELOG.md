# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- GitHub Actions CI pipeline (lint + tests).
- Unit tests for the audit calculator and compliance checker.
- Project documentation: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and this changelog.
- Development tooling configuration (`pyproject.toml`, `.editorconfig`, `Makefile`).

## [0.1.0] - 2026-09-21

### Added

- **Invoice Audit Calculator** for the US, UK, and Germany with worker-type-aware employer social contributions.
- **AI Invoice Compliance Checker** with a jurisdiction-aware rule engine and a deterministic mock-LLM narrative.
- **Asynchronous Audit Log** with faceted filtering, KPI tiles, and CSV export.
- Remote.com-inspired Streamlit dark theme and single-file application architecture.

[Unreleased]: https://github.com/SergeyGer/remote-billing-audit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/SergeyGer/remote-billing-audit/releases/tag/v0.1.0
