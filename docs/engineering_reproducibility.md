# Engineering and Reproducibility

## CI

The repo includes a GitHub Actions workflow in `.github/workflows/ci.yml` that runs:

- package installation,
- pytest,
- core CLI help smoke tests.

## Provenance

Major output folders now include:

```text
provenance.json
```

This records:

- timestamp,
- package version,
- Python version,
- platform,
- command/config path when available,
- git commit when available.

## Helpful CLI

Run:

```bash
dmdc --help
dmdc inspect-data --help
dmdc validate --help
dmdc compare --help
dmdc sweep --help
dmdc continuous --help
```

The recommended workflow remains config-first for reproducibility.
