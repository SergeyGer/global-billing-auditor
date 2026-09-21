# Contributing

Thanks for your interest in improving the **Global Billing & Invoice Compliance Auditor**.

## Getting started

1. Fork and clone the repository.
2. Create a virtual environment and install the development dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

3. Run the app locally:

   ```bash
   streamlit run app.py
   ```

## Development workflow

1. Create a feature branch: `git checkout -b feat/short-description`.
2. Make your change and add or update tests under `tests/`.
3. Make sure the checks pass locally:

   ```bash
   ruff check .
   pytest
   ```

4. Commit using [Conventional Commits](https://www.conventionalcommits.org/) where possible
   (e.g. `feat:`, `fix:`, `docs:`, `test:`, `chore:`).
5. Open a pull request and complete the template.

## Guidelines

- Keep the application dependency-light and the core logic deterministic and testable.
- Prefer small, focused pull requests with a clear description of the change and its motivation.
- Update `README.md` and `CHANGELOG.md` when you change behaviour or add features.
- Do not commit real tax, banking, credential, or personally identifiable data.

## Reporting issues

Use the provided issue templates for bugs and feature requests. For security vulnerabilities,
follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
