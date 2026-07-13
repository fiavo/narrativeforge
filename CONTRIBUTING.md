# Contributing to NarrativeForge

Thanks for your interest in contributing! 
## Setup

See the [Installation](README.md#installation) section in the README. For development, install the Python engine in editable mode with the dev extras so you get `pytest` and `ruff`:

```bash
cd src/NarrativeForge/Engine
pip install -e ".[dev]"
```

## Testing

```bash
# Python
cd src/NarrativeForge/Engine
python -m pytest tests/ -v

# C#
dotnet test src/NarrativeForge/NarrativeForge.Tests/
```

Add or update tests for any change to `Engine/`. Changes to the pipeline orchestrator or consistency checker should include a test that exercises routing/classification, not just the happy path.

## Code Style

- Python: linted with `ruff` (`ruff check src/ tests/`), type hints expected on new public functions.
- C#: follow the existing MVVM structure â€” logic in `ViewModels/`, not code-behind.

## Plugins

Plugins (`Engine/plugins/`, see `plugins/example-agent/` for a reference) are loaded as executable Python code with no sandboxing. If you're contributing one, keep it minimal and well-documented so it's easy to review.

## Pull Requests

1. Make sure tests pass and `ruff check` is clean.
2. Describe what changed and why, and link the related issue if there is one.
3. Keep PRs focused â€” one logical change per PR.

## Bugs & Feature Requests

Open a [GitHub Issue](https://github.com/fiavo/narrativeforge/issues). For bugs, include steps to reproduce and your OS/Python/.NET versions. For features, describe the use case.
