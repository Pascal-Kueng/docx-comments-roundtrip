# Suggested Changes for docx-comments-roundtrip

This document outlines recommended improvements to increase the robustness, portability, and maintainability of the repository.

## Completed

### Restore Nested Word Comments (No Flattening)
Implemented (Feb 2026).

- `md -> docx` now reconstructs native threaded Word comments.
- Reply links are written through `w15:parentId` in `word/comments.xml` and
  `w15:paraIdParent` in `word/commentsExtended.xml`.
- Roundtrip tests assert parent-map parity and reply linkage preservation.

## 1. High Priority

### Fix Test Portability
The test suite currently hardcodes `/tmp` in `tempfile.mkdtemp` calls.
- **Problem:** This causes failures on Windows and other systems without a global `/tmp`.
- **Fix:** Remove the `dir="/tmp"` argument to allow the OS-default temporary directory to be used.

### Modernize Packaging (Cross-Platform Entry Points)
The current Bash wrappers and `Makefile` are not native to Windows.
- **Action:** Create a `pyproject.toml` and convert the project into a proper Python package.
- **Benefit:** 
    - Use `project.scripts` to define `docx-comments`, `docx2md`, and `md2docx` as cross-platform entry points (Windows `.exe` wrappers are created automatically by `pip`).
    - Standardize dependency management.
    - Replace `make test` with a Python-native runner like `pytest` or `tox`/`nox` for cross-platform CI.

## 2. Medium Priority

### Modularize the Codebase
The `docx-comments` script is over 3,000 lines, making it difficult to maintain.
- **Action:** Split the monolithic script into a package:
    - `core/docx.py`: OOXML parsing and manipulation.
    - `core/markdown.py`: Pandoc AST transformations and milestone handling.
    - `core/roundtrip.py`: High-level conversion orchestration.
    - `cli.py`: Argument parsing and environment checks.

### Transition to Pandoc Filters
The current logic relies heavily on regex to manipulate Markdown text.
- **Problem:** Regex is brittle against complex Markdown (escaped characters, nested spans, etc.).
- **Solution:** Implement a native Pandoc Lua filter (or a Python filter via `panflute`) to handle comment spans and milestone markers directly in the AST.

### Hardening: Standard Logging
- **Action:** Replace `print(..., file=sys.stderr)` with the Python `logging` module.
- **Benefit:** Allows users to control verbosity (e.g., `-v` for debug logs) and provides a cleaner way to capture errors during batch processing.

## 3. Low Priority

### CI/CD Implementation
- **Action:** Add a `.github/workflows/test.yml` to run tests on every push across Linux, Mac, and Windows.

### Metadata Preservation
- **Action:** Optionally extract Word document properties (Author, Title, Created Date) and store them in a Markdown YAML frontmatter, then restore them during `md -> docx`.

### Comprehensive Type Hinting
- **Action:** Complete the type hinting across the codebase and integrate `mypy` into the test suite/CI.
