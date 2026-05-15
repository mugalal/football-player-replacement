"""
Document Modification Engine — Adapted from Magdaci's modify_doc/enrich_doc

Two operations supported:
    1. SUBSTITUTE: change a field value in a token (e.g., shot outcome 'on' → 'goal')
    2. INSERT: add a rare modifier token next to base tokens (e.g., add 'cut_inside_right' after wide carries)

Token format reminder (V2):
    shot|z18|on|r|open|xg_l|close          ← shot in z18, outcome 'on', right foot, open play, xg low, close
    pass|z9_z14|s|r|g|short                 ← pass from z9 to z14, success, right foot, ground, short
    carry|z9_z14|fwd                        ← carry forward
    pressure|z21|cp                         ← pressure in z21, counter-press
    progressive_pass                        ← rare modifier (no fields)
    cut_inside_right                        ← rare modifier (no fields)

Field positions per event type are fixed and known.
"""

import random
from copy import deepcopy
from typing import List, Dict, Callable, Optional


# ==================================================================================================
# FIELD SCHEMAS — position of each field in tokens
# ==================================================================================================

FIELD_SCHEMAS = {
    "shot":          {"zone": 1, "outcome": 2, "body": 3, "type": 4, "xg": 5, "dist": 6},
    "pass":          {"zones": 1, "outcome": 2, "body": 3, "height": 4, "length": 5},
    "carry":         {"zones": 1, "direction": 2},
    "dribble":       {"zone": 1, "outcome": 2},
    "pressure":      {"zone": 1, "type": 2},  # type = 'cp' or 'reg'
    "duel":          {"zone": 1, "type": 2, "outcome": 3},
    "interception":  {"zone": 1, "outcome": 2},
    "ball_recovery": {"zone": 1, "outcome": 2},
    "clearance":     {"zone": 1, "body": 2},
}


def parse_token(token: str) -> Optional[Dict]:
    """
    Parse a base token into its event type and fields.
    Returns None for rare modifiers (no pipe character) or unknown tokens.
    """
    if "|" not in token:
        return None  # rare modifier, no fields

    parts = token.split("|")
    event_type = parts[0]

    if event_type not in FIELD_SCHEMAS:
        return None

    return {
        "event": event_type,
        "parts": parts,
        "schema": FIELD_SCHEMAS[event_type],
    }


def rebuild_token(parsed: Dict) -> str:
    """Reverse of parse_token."""
    return "|".join(parsed["parts"])


# ==================================================================================================
# INTERVENTION TYPES
# ==================================================================================================

class Intervention:
    """Base class for all document interventions."""

    def __init__(self, probability: float = 1.0, name: str = ""):
        self.probability = probability
        self.name = name

    def apply(self, doc: List[str]) -> List[str]:
        raise NotImplementedError


class SubstituteField(Intervention):
    """
    Change a field value in matching tokens.

    Example: SubstituteField('shot', 'outcome', 'on', 'goal', probability=0.5)
        → Half of 'on' shots become 'goal' shots

    Optional `condition` lets you gate substitution on additional fields.
    Example: only substitute lost AERIAL duels (not ground ones):
        SubstituteField('duel', 'outcome', 'lost', 'won',
                        probability=0.5,
                        condition=lambda p: p['parts'][2] == 'aerial')
    """

    def __init__(
        self,
        event: str,
        field: str,
        from_value: str,
        to_value: str,
        probability: float = 1.0,
        name: str = "",
        condition: Optional[Callable[[Dict], bool]] = None,
    ):
        super().__init__(probability, name or f"sub_{event}_{field}_{from_value}_to_{to_value}")
        self.event = event
        self.field = field
        self.from_value = from_value
        self.to_value = to_value
        self.condition = condition

        if event not in FIELD_SCHEMAS or field not in FIELD_SCHEMAS[event]:
            raise ValueError(f"Unknown field: {event}.{field}")

        self.field_idx = FIELD_SCHEMAS[event][field]

    def apply(self, doc: List[str]) -> List[str]:
        new_doc = []
        for token in doc:
            parsed = parse_token(token)
            if parsed is None or parsed["event"] != self.event:
                new_doc.append(token)
                continue

            if parsed["parts"][self.field_idx] != self.from_value:
                new_doc.append(token)
                continue

            # Apply optional condition gate
            if self.condition is not None:
                try:
                    if not self.condition(parsed):
                        new_doc.append(token)
                        continue
                except (KeyError, IndexError):
                    new_doc.append(token)
                    continue

            if random.random() < self.probability:
                parsed["parts"][self.field_idx] = self.to_value
                new_doc.append(rebuild_token(parsed))
            else:
                new_doc.append(token)

        return new_doc


class InsertModifier(Intervention):
    """
    Insert a rare modifier token next to tokens matching a condition.

    Example: InsertModifier('cut_inside_right', condition=lambda t: ...)
        → Adds 'cut_inside_right' token after qualifying tokens

    The condition is a function that receives a parsed token and returns bool.
    """

    def __init__(
        self,
        modifier_token: str,
        condition: Callable[[Dict], bool],
        probability: float = 1.0,
        name: str = "",
    ):
        super().__init__(probability, name or f"insert_{modifier_token}")
        self.modifier_token = modifier_token
        self.condition = condition

    def apply(self, doc: List[str]) -> List[str]:
        new_doc = []
        for token in doc:
            new_doc.append(token)
            parsed = parse_token(token)
            if parsed is None:
                continue

            try:
                matches = self.condition(parsed)
            except (KeyError, IndexError):
                matches = False

            if matches and random.random() < self.probability:
                new_doc.append(self.modifier_token)

        return new_doc


# ==================================================================================================
# PRE-DEFINED INTERVENTIONS — composable building blocks for searches
# ==================================================================================================

def upgrade_finishing(probability: float = 0.5) -> List[Intervention]:
    """Convert non-goal shots to goals. Models 'more clinical finishing'."""
    return [
        SubstituteField("shot", "outcome", "on",  "goal", probability, "upgrade_shots_on"),
        SubstituteField("shot", "outcome", "off", "goal", probability, "upgrade_shots_off"),
    ]


def add_cut_inside(probability: float = 0.6) -> List[Intervention]:
    """
    Insert cut_inside_right after carries that start in right wide area (z5/10/15/20/25).
    Insert cut_inside_left after carries that start in left wide area (z1/6/11/16/21).

    Approximates 'add inverted winger behavior'.
    """
    # Right-side wide zones in our 5x5 grid (column 5 = rightmost)
    right_wide = {"5", "10", "15", "20", "25"}
    left_wide  = {"1", "6", "11", "16", "21"}

    def is_right_wide_carry(parsed):
        if parsed["event"] != "carry":
            return False
        zones = parsed["parts"][1]  # e.g., "z5_z14"
        start_zone = zones.split("_")[0].replace("z", "")
        return start_zone in right_wide

    def is_left_wide_carry(parsed):
        if parsed["event"] != "carry":
            return False
        zones = parsed["parts"][1]
        start_zone = zones.split("_")[0].replace("z", "")
        return start_zone in left_wide

    return [
        InsertModifier("cut_inside_right", is_right_wide_carry, probability, "add_cut_inside_right"),
        InsertModifier("cut_inside_left",  is_left_wide_carry,  probability, "add_cut_inside_left"),
    ]


def add_progression(probability: float = 0.4) -> List[Intervention]:
    """Boost progressive carries and passes. Models 'more direct ball progression'."""

    def is_forward_carry(parsed):
        return parsed["event"] == "carry" and parsed["parts"][2] == "fwd"

    def is_pass(parsed):
        return parsed["event"] == "pass" and parsed["parts"][2] == "s"  # successful only

    return [
        InsertModifier("progressive_carry", is_forward_carry, probability, "add_progressive_carry"),
        InsertModifier("progressive_pass",  is_pass,          probability, "add_progressive_pass"),
    ]


def boost_pressing(probability: float = 0.7) -> List[Intervention]:
    """Convert regular pressure to counter-press. Models 'Klopp-style gegenpressing'."""
    return [
        SubstituteField("pressure", "type", "reg", "cp", probability, "boost_pressure_to_cp"),
    ]


def add_chance_creation(probability: float = 0.4) -> List[Intervention]:
    """Insert key_pass after successful passes to box-adjacent zones."""
    box_zones = {"23", "24", "25", "18", "19", "20"}  # final third zones in our 5x5

    def is_pass_to_box_area(parsed):
        if parsed["event"] != "pass" or parsed["parts"][2] != "s":
            return False
        zones = parsed["parts"][1]  # e.g., "z9_z23"
        end_zone = zones.split("_")[1].replace("z", "")
        return end_zone in box_zones

    return [
        InsertModifier("key_pass", is_pass_to_box_area, probability, "add_key_pass"),
    ]


def enrich_dribbling(probability: float = 0.5) -> List[Intervention]:
    """Convert failed dribbles to successful, add dribble_in_box modifiers."""

    def is_in_box_dribble(parsed):
        if parsed["event"] != "dribble":
            return False
        zone = parsed["parts"][1].replace("z", "")
        return zone in {"23", "24", "25"}

    return [
        SubstituteField("dribble", "outcome", "f", "s", probability, name="complete_dribbles"),
        InsertModifier("dribble_in_box", is_in_box_dribble, probability, "add_dribble_in_box"),
    ]


# ==================================================================================================
# DEFENSIVE INTERVENTIONS
# ==================================================================================================

def aerial_dominance(probability: float = 0.5) -> List[Intervention]:
    """
    Convert lost aerial duels to won. Models 'aerial threat / defensive heading specialist'.

    Use case: Find target strikers (Benteke, Giroud), aerial-strong CBs, set-piece threats.

    Implementation note: We use a condition gate to ONLY affect aerial duels.
    Ground duels stay untouched — those are a different skill (ball winning).
    """
    def is_aerial(parsed):
        # Field 2 is duel type; aerial vs ground
        return parsed["parts"][2] == "aerial"

    return [
        SubstituteField(
            "duel", "outcome", "lost", "won",
            probability=probability,
            condition=is_aerial,
            name="win_aerial_duels",
        ),
    ]


def ball_winning(probability: float = 0.5) -> List[Intervention]:
    """
    Convert lost ground defensive actions to won. Models 'defensive midfielder ball-winner'.

    Affects:
        - Ground duels (field 2 = ground)
        - Interceptions
        - Ball recoveries

    Use case: Find ball-winners like Kanté, Casemiro, Wanyama, Vidal-types.

    Note: This is partially a quality bump (winning more) but it's also a tactical
    profile — some players are TASKED with winning the ball, others aren't. The
    intervention shifts the search toward players whose token distributions look
    like ball-winners.
    """
    def is_ground(parsed):
        return parsed["parts"][2] == "ground"

    return [
        SubstituteField(
            "duel", "outcome", "lost", "won",
            probability=probability,
            condition=is_ground,
            name="win_ground_duels",
        ),
        SubstituteField(
            "interception", "outcome", "lost", "won",
            probability=probability,
            name="win_interceptions",
        ),
        SubstituteField(
            "ball_recovery", "outcome", "f", "s",
            probability=probability,
            name="successful_recoveries",
        ),
    ]


# ==================================================================================================
# APPLY INTERVENTIONS TO A DOCUMENT
# ==================================================================================================

def modify_doc(doc: List[str], interventions: List[Intervention]) -> List[str]:
    """Apply a list of interventions sequentially to a document."""
    result = list(doc)
    for intervention in interventions:
        result = intervention.apply(result)
    return result


def modify_docs(docs: List[List[str]], interventions: List[Intervention]) -> List[List[str]]:
    """Apply interventions to a batch of documents."""
    return [modify_doc(doc, interventions) for doc in docs]