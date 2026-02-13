# Suggested Changes for docx-comments-roundtrip

This document outlines recommended improvements to increase the robustness, portability, and maintainability of the repository.

## Completed

### Restore Nested Word Comments (No Flattening)
Implemented (Feb 2026).

- `md -> docx` now reconstructs native threaded Word comments.
- Reply links are written through `w15:parentId` in `word/comments.xml` and
  `w15:paraIdParent` in `word/commentsExtended.xml`.
- Roundtrip tests assert parent-map parity and reply linkage preservation.

### Fix Test Portability
Implemented (Feb 2026).

- Removed hardcoded `/tmp` paths in tests; now uses `tempfile.gettempdir()`.

### Modernize Packaging (Cross-Platform Entry Points)
Implemented (Feb 2026).

- Added `pyproject.toml` with `project.scripts`.
- Converted project into `src/dmc` package structure.
- Entry points `dmc`, `docx2md`, etc. are now cross-platform.

### Modularize the Codebase
Implemented (Feb 2026).

- Split monolithic script into `src/dmc/converter.py`, `src/dmc/cli.py`, etc.

### CI/CD Implementation
Implemented (Feb 2026).

- Added `.github/workflows/ci.yml`.

## 1. High Priority

### Track Changes / Suggestions Roundtrip
Currently, the tool focuses on comments. It should also support tracked changes (suggested additions/deletions).
- **Goal:** Preserve `w:ins` (insertions) and `w:del` (deletions) through Markdown roundtrip.
- **Challenge:**
    - Nested edits (Author B editing Author A's insertion).
    - Representing this in Markdown (e.g., `[text]{.insertion author="A"}` or `~~deleted~~{.deletion}`).
    - Reconstructing valid OOXML `w:trackRevisions` structures.

## 2. Medium Priority

### Transition to Pandoc Filters
The current logic relies heavily on regex to manipulate Markdown text.
- **Problem:** Regex is brittle against complex Markdown (escaped characters, nested spans, etc.).
- **Solution:** Implement a native Pandoc Lua filter (or a Python filter via `panflute`) to handle comment spans and milestone markers directly in the AST.

### Hardening: Standard Logging
- **Action:** Replace `print(..., file=sys.stderr)` with the Python `logging` module.
- **Benefit:** Allows users to control verbosity (e.g., `-v` for debug logs) and provides a cleaner way to capture errors during batch processing.

## 3. Low Priority

### Metadata Preservation
- **Action:** Optionally extract Word document properties (Author, Title, Created Date) and store them in a Markdown YAML frontmatter, then restore them during `md -> docx`.

### Comprehensive Type Hinting
- **Action:** Complete the type hinting across the codebase and integrate `mypy` into the test suite/CI.
