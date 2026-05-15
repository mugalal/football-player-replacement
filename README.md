# Player Replacement

Player Replacement is an experimental football scouting system for finding player replacements and profile upgrades from event-data embeddings.

The most mature path is the `gp2` pipeline. It builds separate on-ball and off-ball player-match representations, combines them into Player2Vec vectors, and validates the search method against the 2016 Liverpool/Sadio Mane recruitment case.

## What It Does

- Tokenizes StatsBomb-style event data into football-aware action tokens.
- Builds action, player-match, and player-level embeddings.
- Separates on-ball and off-ball behavior before combining player vectors.
- Supports replacement search from one or more source players.
- Supports profile interventions such as finishing, progression, chance creation, dribbling, pressing, and aerial dominance.
- Includes a historical validation case where the system searches for a Klopp-style attacking signing and should rank Sadio Mane highly.

## Repository Layout

```text
src/gp2/
  evaluation/   Scouting engine, CLI helpers, validation scripts
  model/        Training and Player2Vec build scripts
  pipeline/     Corpus and player metadata builders
  preprocess/   Tokenization and sequence helpers
  paths.py      Project-root-aware artifact paths

scripts/
  rebuild_venv.ps1   Recreate the Python 3.11 environment
  validate_gp2.ps1   Run the GP2 Mane validation with UTF-8 output

docs/
  MODEL_ARTIFACTS.md Artifact expectations and storage guidance
```

Older GP1 and Transformer experiments are still present under `src/gp1`, `src/model`, and `src/preprocess`, but GP2 is the recommended system.

## Requirements

- Python 3.11
- Windows PowerShell for the provided setup scripts
- Local model/data artifacts under `models/gp2/` for evaluation commands

Raw data, generated corpora, trained models, visualizations, and local environments are intentionally ignored by Git. See [docs/MODEL_ARTIFACTS.md](docs/MODEL_ARTIFACTS.md).

## Setup

Recommended on Windows:

```powershell
cd path\to\player-replacement
powershell -ExecutionPolicy Bypass -File .\scripts\rebuild_venv.ps1
```

Manual setup:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

Optional notebook support:

```powershell
python -m pip install -r requirements-notebooks.txt
```

## Validate

Run the GP2 regression check:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate_gp2.ps1
```

Expected outcome: Sadio Mane appears near the top of the attacker shortlist for the Liverpool 2015-16 attacking profile.

You can also run the module directly:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m src.gp2.evaluation.mane_case_validation
```

## Main GP2 Pipeline

When raw data is available locally, the intended rebuild order is:

```powershell
.\.venv\Scripts\python.exe -m src.gp2.pipeline.extract_players
.\.venv\Scripts\python.exe -m src.gp2.pipeline.build_action_corpus
.\.venv\Scripts\python.exe -m src.gp2.model.train_action2vec
.\.venv\Scripts\python.exe -m src.gp2.pipeline.build_player_match_corpus
.\.venv\Scripts\python.exe -m src.gp2.model.train_playermatch2vec
.\.venv\Scripts\python.exe -m src.gp2.model.build_player2vec_split
.\.venv\Scripts\python.exe -m src.gp2.evaluation.mane_case_validation
```

## Notes

The code now resolves GP2 artifact paths from the project root through `src/gp2/paths.py`, so GP2 commands can be run from outside the repository as long as the local artifact files exist in the expected project folder.
