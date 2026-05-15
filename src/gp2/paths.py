from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
VISUALIZATIONS_DIR = PROJECT_ROOT / "visualizations"

GP2_MODELS_DIR = MODELS_DIR / "gp2"
TOP5_DATA_DIR = DATA_DIR / "Top5_Leagues_1516"
FULL_MATCHES_DIR = DATA_DIR / "Full_Matches"

ACTION_SENTENCES_PATH = GP2_MODELS_DIR / "action_sentences.jsonl"
ACTION2VEC_PATH = GP2_MODELS_DIR / "action2vec.model"
PLAYER_INFO_PATH = GP2_MODELS_DIR / "player_info.json"
PLAYER_MATCH_DOCS_PATH = GP2_MODELS_DIR / "player_match_docs_split.jsonl"
PLAYER_MATCH_DOCS_LEGACY_PATH = GP2_MODELS_DIR / "player_match_docs.jsonl"
PLAYER2VEC_PATH = GP2_MODELS_DIR / "player2vec_64d.npz"
PLAYER_METADATA_PATH = GP2_MODELS_DIR / "player_metadata_v2.json"
ONBALL_MODEL_PATH = GP2_MODELS_DIR / "playermatch2vec_onball.model"
OFFBALL_MODEL_PATH = GP2_MODELS_DIR / "playermatch2vec_offball.model"

PLAYER2VEC_UMAP_PATH = VISUALIZATIONS_DIR / "player2vec_umap.png"

# Backward-compatible names used by older GP2 scripts.
DOCS_PATH = PLAYER_MATCH_DOCS_PATH
