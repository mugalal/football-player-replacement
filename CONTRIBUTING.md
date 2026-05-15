# Contributing

## Setup

Use Python 3.11. On Windows, the recommended setup is:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\rebuild_venv.ps1
```

## Validation

After placing or regenerating the GP2 artifacts under `models/gp2/`, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_gp2.ps1
```

The validation checks the historical Liverpool 2016 Sadio Mane replacement case.

## Repository Hygiene

Do not commit:

- `.venv/`
- `.tmp/`
- raw event data
- generated corpora
- trained model files
- plots, reports, or presentation exports

Keep code, documentation, and small configuration files in Git. Store large artifacts outside Git or attach them to GitHub releases.
