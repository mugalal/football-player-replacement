"""
Mané-validation preset, reproduced from `src/gp2/evaluation/mane_case_validation.py`.

Reproduced verbatim (not imported) because we don't want to call the
script's `validate()` function — it has print-heavy reporting side effects
and a different return contract. The constants here are the regression
checkpoint; if they drift from the engine's expectations, that's intentional
breakage to be reviewed.
"""
from __future__ import annotations

# Six sources — Coutinho was removed in the engine's regression file
# (mane_case_validation.py:37, comment "##coutinho removed").
LIVERPOOL_2015_16_ATTACKERS: list[str] = [
    "Lallana",
    "Firmino",
    "Sturridge",
    "Origi",
    "Ibe",
    "Benteke",
]

KLOPP_UPGRADES_VALIDATED: dict[str, float] = {
    "cut_inside": 0.7,
    "finishing": 0.5,
    "progression": 0.4,
    "chance_creation": 0.4,
    "dribbling": 0.4,
    "pressing": 0.7,
}

DEFENDER_POSITIONS: set[str] = {
    "Goalkeeper",
    "Center Back",
    "Left Center Back",
    "Right Center Back",
    "Left Back",
    "Right Back",
    "Left Wing Back",
    "Right Wing Back",
}

MANE_TOP_K: int = 60
MANE_SEED: int = 42
MANE_FINAL_TOP_N: int = 30
