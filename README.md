# docx-md-comments

`docx-md-comments` is a DOCX to Markdown converter and Markdown to DOCX converter for one specific problem: preserving Microsoft Word comments through roundtrip edits.

It is built for workflows where you:

1. start with a Word `.docx` containing comments
2. edit content in Markdown (manually or with an LLM)
3. convert back to Word without losing comment structure

## At A Glance

| Capability | Supported |
| --- | --- |
| DOCX -> Markdown conversion | Yes |
| Markdown -> DOCX conversion | Yes |
| Comment anchors | Preserved |
| Threaded replies | Preserved |
| Comment state (active/resolved) | Preserved |
| Native Word comment thread reconstruction | Yes |

## Why This Is Useful

Most generic converters drop or flatten comment metadata. This project is focused on Word review workflows, so comments remain usable after conversion.

Common use cases:

- legal, scientific, or editorial review drafts with heavy comment threading
- LLM-assisted editing of reviewed documents
- roundtrip pipelines where Word comments must survive intact

## Before You Start

Requirements:

- Python 3.10+
- Pandoc installed and available on `PATH`

Install Pandoc:

- macOS: `brew install pandoc`
- Ubuntu/Debian: `sudo apt-get install pandoc`
- Windows (PowerShell): `choco install pandoc -y`

## Install

Recommended (`pipx`, isolated app install):

```bash
pipx install docx-md-comments
```

Alternative (`pip`):

```bash
python -m pip install docx-md-comments
```

Installed commands:

- `dmc`
- `docx-comments`
- `docx2md` / `d2m`
- `md2docx` / `m2d`

## Update To Latest Version

If installed with `pipx`:

```bash
pipx upgrade docx-md-comments
```

If installed with `pip`:

```bash
python -m pip install --upgrade docx-md-comments
```

## Quick Start

Convert Word to Markdown:

```bash
dmc draft.docx
```

Creates `draft.md`.

Convert Markdown back to Word:

```bash
dmc draft.md
```

Creates `draft.docx`.

## LLM Editing Workflow

1. Convert reviewed Word document to Markdown:

```bash
dmc reviewed.docx
```

2. Edit `reviewed.md` manually or with an LLM.
3. Convert back to Word:

```bash
dmc reviewed.md
```

4. Open `reviewed.docx` in Word and continue normal comment-based review.

## Command Variants

DOCX -> Markdown:

```bash
docx-comments draft.docx
docx2md draft.docx
d2m draft.docx
```

Markdown -> DOCX:

```bash
md2docx draft.md
m2d draft.md
```

### Explicit input/output paths

DOCX -> Markdown:

```bash
docx2md draft.docx -o draft.md
d2m draft.docx -o draft.md
dmc docx2md draft.docx -o draft.md
```

Markdown -> DOCX:

```bash
md2docx draft.md -o draft.docx
m2d draft.md -o draft.docx
dmc md2docx draft.md -o draft.docx
```

Use a reference Word document for styling:

```bash
md2docx draft.md --ref original.docx -o final.docx
m2d draft.md -r original.docx -o final.docx
```

`--ref` maps to Pandoc `--reference-doc`.

### Pass-through Pandoc arguments (advanced)

Unknown flags are passed through to Pandoc:

```bash
docx2md draft.docx -o draft.md --extract-media=media
dmc md2docx draft.md --reference-doc=template.docx
```

## Limitations

- **Tracked Changes:** Word revisions are not preserved through roundtrip. Resolve them in Word first.
- **Formatting:** This project prioritizes comment fidelity. Very complex layouts may not roundtrip perfectly.

## Help

```bash
dmc --help
docx2md --help
md2docx --help
```

## For Contributors: Testing

Run full suite:

```bash
make test
```

Roundtrip-focused tests only:

```bash
make test-roundtrip
```

`make test` also writes:

- `artifacts/out_test.md`
- `artifacts/out_test.docx`

## Report Issues

Please open bugs/feature requests at:

https://github.com/Pascal-Kueng/docx-md-comments/issues

When reporting a conversion bug, include:

- input sample (or minimal repro)
- command used
- expected vs actual behavior (Word view)
- failing `failure_bundle` path if tests failed

## Technical Notes (Brief)

- Marker style uses `///C<ID>.START///` / `///C<ID>.END///` (optional `==...==` wrapper).
- Reply relationships are reconstructed as native Word threads (`commentsExtended.xml` `paraIdParent` + story markers).
- Validation fails fast on malformed marker edits with line-specific diagnostics.

For maintainer details, see `AGENTS.md`.
