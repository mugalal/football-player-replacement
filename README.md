# Replacement Scout

A production-style web app for football scouting built on the GP2 methodology:
on-ball/off-ball player-match embeddings, with a documented historical
regression that recovers Liverpool's actual 2016 signing of Sadio Mané.

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│  Next.js 14      │    │  FastAPI         │    │  GP2 scouting engine │
│  (frontend)      │───▶│  (backend)       │───▶│  src/gp2/ (locked)   │
│  Vercel          │    │  HF Spaces       │    │                      │
└──────────────────┘    └──────────────────┘    └──────────────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────┐
                                              │  models/gp2/         │
                                              │  (Git LFS on Space,  │
                                              │   mounted locally)   │
                                              └──────────────────────┘
```

The frontend deploys to Vercel; the backend deploys to a Hugging Face Space
(Docker SDK). Local development runs the whole stack via Docker Compose,
which is also the official presentation fallback if the public Space is
asleep or down.

## GP2 methodology

The locked engine in `src/gp2/` is unmodified by the web app — the
FastAPI service is a thin wrapper that imports it via `sys.path`. The
methodology, in short:

1. **Tokenize** StatsBomb-style event data into football-aware action
   tokens.
2. **Split on-ball vs off-ball** behavior. Off-ball patterns (pressing,
   defensive positioning) get their own corpus and Doc2Vec model;
   on-ball patterns (passing, dribbling, shooting) get another. Mixing
   them at the token level discards information.
3. Train **player-match Doc2Vec** models — each player-match becomes a
   document.
4. Build **Player2Vec** by averaging per-match vectors per player; this
   is the 64-dim representation used for similarity search.
5. Support **profile interventions** (Magdaci-style) — modify a source
   player's match tokens, re-infer per match, average — so the search
   target can be "Lallana, but with finishing".
6. **Validation**: given Liverpool's 2015-16 attackers and Klopp-style
   upgrades (cut-inside, finishing, progression, chance creation,
   dribbling, pressing), the methodology should rank Sadio Mané — their
   actual 2016 signing — high among attacking candidates from ~2,200
   players. Defensive positions are post-filtered (Klopp's brief was
   for an attacker, not a CB).

This regression is exposed at `/api/validations/mane` and rendered at
`/validations/mane`.

## Repository layout

```text
backend/                 FastAPI service (imports src/gp2 via sys.path)
  app/                   routes, schemas, services, static
  Dockerfile             local docker-compose; assumes models/ is volume-mounted
  requirements.txt       pinned to the working local .venv
  tests/test_smoke.py    3 model-independent smoke tests

frontend/                Next.js 14 App Router, TypeScript strict
  app/                   /, /replace, /brief, /player/[id], /validations/mane
  components/            ui (shadcn-style), search, player, layout, common
  lib/                   api/, hooks/, types.ts, utils.ts

hf-space/                Hugging Face Space deploy assets (Dockerfile + .dockerignore + README)

src/gp2/                 Locked ML engine — DO NOT EDIT
  evaluation/            scouting_engine.py, modify_doc.py, mane_case_validation.py
  model/                 training + Player2Vec build scripts
  pipeline/              corpus + metadata builders
  preprocess/            tokenization helpers
  paths.py               project-root-aware artifact paths

models/gp2/              Runtime artifacts (gitignored, ~152 MB)
docker-compose.yml       local dev: backend + frontend
.dockerignore            root — EXCLUDES models/ for local builds
```

The older GP1 / Transformer experiments under `src/gp1/`, `src/model/`,
`src/preprocess/` are still present but GP2 is the system the web app
uses.

## Quickstart (local Docker)

**Prerequisites:**
- Docker Desktop running
- `models/gp2/` populated locally (see "Model artifacts" below)
- Node 20+ only if you want to run the frontend outside Docker

```powershell
docker compose up
```

URLs:
- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- OpenAPI docs: <http://localhost:8000/docs>

First boot warms the engine (~5–15 s; you'll see "Warming up backend..."
in the UI). Once `engine_state` is `ready`, the banner disappears.

To stop:

```powershell
docker compose down
```

## Quickstart (without Docker)

Backend:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r backend\requirements.txt
python -m pip install -e . --no-deps

# Start the API (port 8000):
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend (in a second shell):

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

## Verify

The fastest end-to-end verification:

```powershell
curl http://localhost:8000/api/health
# {"status":"ok","engine_loaded":true,"engine_state":"ready",...}

curl http://localhost:8000/api/upgrades
# {"onball":[...], "offball":[...]}

curl "http://localhost:8000/api/players?q=man%C3%A9&limit=5"   # q=mané
# [{"player_id":"3629","name":"Sadio Mané",...}]

curl http://localhost:8000/api/validations/mane
# {"verdict":"EXCELLENT","mane_rank":5,...} after ~30-60s first call
```

The engine's player matcher is plain lowercased-Unicode substring — use
the accented form `q=mané` (URL-encoded `q=man%C3%A9`); plain `q=mane`
returns no results because `'e' ≠ 'é'`.

You can also run the original CLI regression check (uses `src/gp2/` directly,
not through the API):

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m src.gp2.evaluation.mane_case_validation
```

Smoke tests (work without models present):

```powershell
cd backend
python -m pytest -q
```

## Deployment

### Frontend → Vercel

1. Push the repo to GitHub.
2. In Vercel, **Import Project**, set **Root Directory** to `frontend/`.
3. Project Settings → Environment Variables, add
   `NEXT_PUBLIC_API_URL` = `https://<your-space>.hf.space`.
4. Vercel auto-deploys on push to `main`. `NEXT_PUBLIC_*` env vars are
   baked into the bundle at build time.

### Backend → Hugging Face Spaces

See [hf-space/README.md](hf-space/README.md) for the full step-by-step. In
summary:

1. Create a new Space (Docker SDK, blank template).
2. Clone the Space repo locally.
3. Copy `hf-space/Dockerfile` and `hf-space/.dockerignore` into the
   Space repo root, plus `backend/`, `src/`, and `models/`.
4. `git lfs install`, `git lfs track "models/**"`, commit, push.

The free CPU Basic tier (2 vCPU / 16 GB RAM) is sufficient — warm-engine
RSS is ~600 MB locally. Free Spaces may sleep after inactivity (per
[HF Spaces overview](https://huggingface.co/docs/hub/spaces-overview));
the frontend's `BackendStatusBanner` surfaces warming/unavailable/unreachable
states.

## Model artifacts

The engine reads exactly five files at inference time (~152 MB total):

| File                                    | Size      | When read              |
|-----------------------------------------|-----------|------------------------|
| `models/gp2/player2vec_64d.npz`         |  1.1 MB   | startup                |
| `models/gp2/player_metadata_v2.json`    |  0.9 MB   | startup                |
| `models/gp2/playermatch2vec_onball.model`| 13.7 MB  | startup                |
| `models/gp2/playermatch2vec_offball.model`| 4.6 MB  | startup                |
| `models/gp2/player_match_docs_split.jsonl`| 131.8 MB| upgrade searches only  |

Training-only artifacts (`action_sentences.jsonl` 211 MB and
`action2vec.model` 2.8 MB) are **not** needed by the serving image —
verified by grep across `src/gp2/evaluation/`.

The full pipeline rebuild order (when raw data is available locally):

```powershell
.\.venv\Scripts\python.exe -m src.gp2.pipeline.extract_players
.\.venv\Scripts\python.exe -m src.gp2.pipeline.build_action_corpus
.\.venv\Scripts\python.exe -m src.gp2.model.train_action2vec
.\.venv\Scripts\python.exe -m src.gp2.pipeline.build_player_match_corpus
.\.venv\Scripts\python.exe -m src.gp2.model.train_playermatch2vec
.\.venv\Scripts\python.exe -m src.gp2.model.build_player2vec_split
.\.venv\Scripts\python.exe -m src.gp2.evaluation.mane_case_validation
```

See [docs/MODEL_ARTIFACTS.md](docs/MODEL_ARTIFACTS.md) for artifact
storage details.

## Optional: player photos and team logos

The UI works fully without images — `PlayerAvatar` falls back to
deterministic initials in a colored circle. If you want photos:

```powershell
python backend\scripts\fetch_wikidata_images.py
```

The script queries Wikidata for player photos and team logos, rate-limited
to 1 req/sec. Expect ~70% coverage for players, ~95% for teams, and
~30–45 minutes for the full dataset. Resumable (skips existing files).

## Caveats

- **In-memory job store.** Searches in progress are lost on backend
  restart. Acceptable for a v1 demo; production would need
  Redis/SQLite.
- **HF Spaces free tier may sleep after inactivity.** First request
  after sleep reloads the Python ML stack plus model artifacts; warm-
  engine memory measured around 600 MB locally.
- **CORS regex** `https://.*\.vercel\.app` is permissive — any Vercel
  subdomain may call the backend. Acceptable for this portfolio scope
  because there's no auth and no per-tenant data.
- **Models are excluded from Git.** They live in `models/gp2/` and must
  be populated locally before running, or copied into the HF Space repo
  via Git LFS for deployment.
- **The engine's player matcher is plain Unicode** — `q=mane` doesn't
  match "Sadio Mané" because `'e' ≠ 'é'`. Use accented forms.

## Implementation plan

The full design plan that drove this implementation lives in
`.claude/plans/we-are-making-the-squishy-hickey.md` (local-only, not
committed). The summary: src/gp2/ stays untouched, the backend wraps
the engine through a single-worker ThreadPoolExecutor for structural
concurrency control, and the Mané validation endpoint uses asyncio.Lock
+ double-checked locking on cache-miss to prevent redundant inference.
