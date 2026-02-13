# Publishing Checklist

This is the practical checklist to test and publish `docx-md-comments`.

Primary path: Trusted Publishing via GitHub Actions (`.github/workflows/publish.yml`).

## 0) Finalize repository state

Before publishing:

- Commit packaging/CLI changes.
- Confirm `[project].name` in `pyproject.toml` is correct for PyPI.
- Ensure licensing is consistent (`LICENSE` present and referenced by `pyproject.toml`).

## 1) Pre-release checks

Run from repository root:

```bash
make test
python -m unittest -q tests.test_cli_entrypoints
```

Optional local artifact smoke:

```bash
make roundtrip-example
```

Inspect:

- `artifacts/out_test.md`
- `artifacts/out_test.docx`

## 2) One-time Trusted Publishing setup

Configure trusted publishers in PyPI and TestPyPI.

PyPI publisher settings:

- Owner: `Pascal-Kueng`
- Repository name: `docx-md-comments`
- Workflow name: `publish.yml`
- Environment name: `pypi`

TestPyPI publisher settings:

- Owner: `Pascal-Kueng`
- Repository name: `docx-md-comments`
- Workflow name: `publish.yml`
- Environment name: `testpypi`

Repository side:

- Keep `.github/workflows/publish.yml` in default branch.
- Create GitHub environments `pypi` and `testpypi` (add approval rules if desired).

No PyPI API token or `twine upload` credentials are needed for this path.

## 3) Publish via GitHub Actions

TestPyPI dry run (recommended before production):

1. Open Actions -> `Publish`.
2. Click `Run workflow`.
3. Select `target=testpypi`.
4. Wait for `Publish to TestPyPI` to pass.

Production publish:

1. Create and push a release tag:

```bash
git tag v<VERSION>
git push origin v<VERSION>
```

2. Create a GitHub Release for that tag and click `Publish release`.
3. The `Publish` workflow runs automatically and executes `Publish to PyPI`.

## 4) Verification

Verify install from TestPyPI (after dry run):

```bash
cd /tmp
python -m venv test-pypi-env
source test-pypi-env/bin/activate
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple docx-md-comments
dmc --help
deactivate
rm -rf test-pypi-env
```

Verify install from PyPI:

```bash
pipx install docx-md-comments
dmc --help
```

## 5) Emergency fallback: manual upload

If GitHub OIDC publishing is unavailable, use manual `twine` upload:

```bash
python -m venv .venv-release
source .venv-release/bin/activate
python -m pip install --upgrade pip build twine
rm -rf dist build *.egg-info
python -m build
python -m twine check --strict dist/*
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
deactivate
rm -rf .venv-release dist build *.egg-info
```
