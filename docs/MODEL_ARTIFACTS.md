# Model Artifacts

This repository intentionally does not track trained models, generated corpora, raw data, or visualization outputs.

The GP2 pipeline expects these local files under `models/gp2/` when running evaluation commands:

- `action2vec.model`
- `player2vec_64d.npz`
- `player_metadata_v2.json`
- `player_info.json`
- `player_match_docs_split.jsonl`
- `playermatch2vec_onball.model`
- `playermatch2vec_offball.model`

These files are generated from StatsBomb-style event JSON data and can be large. Keep them local, store them in a release asset, or publish them through an external artifact store instead of committing them to Git.

The current code resolves artifact paths from the project root through `src/gp2/paths.py`, so commands can be run from outside the repository as long as the local project folder still contains the expected `models/gp2/` files.
