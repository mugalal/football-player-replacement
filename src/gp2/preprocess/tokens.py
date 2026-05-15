"""
Updated Tokenization for Player2Vec — V2

NEW SEMANTIC TOKENS (added to existing base tokens):

  CARRY:
    - cut_inside_right    : started touchline-right (y>60), ended central (25-55), forward
    - cut_inside_left     : started touchline-left  (y<20), ended central (25-55), forward
    - carry_to_box        : ended in penalty area (x>102, 18<=y<=62)
    - carry_to_final_third: ended in attacking third (x>80) but not box

  PASS:
    - pass_to_box         : ended in penalty area
    - pass_to_final_third : crossed into final third (started x<80, ended x>80)
    - key_pass            : StatsBomb shot_assist=True (created shot)
    - assist              : StatsBomb goal_assist=True (created goal)

  DRIBBLE:
    - dribble_right_wide  : performed in right wing zone (y>60)
    - dribble_left_wide   : performed in left wing zone (y<20)
    - dribble_in_box      : performed in penalty area

  PRESSURE:
    - Now base token includes counterpress: "pressure|z21|cp" or "pressure|z21|reg"
    - Counterpress = Klopp's gegenpressing signature

These are RARE MODIFIERS (except pressure where it's part of base token)
that capture distinctive behaviors without bloating vocabulary.
"""

from .zones import xy_to_zone


# ==================================================================================================
# CONFIG
# ==================================================================================================

PASS_PROGRESSIVE_THRESHOLD = 10
CARRY_PROGRESSIVE_THRESHOLD = 10

# Spatial thresholds (StatsBomb 120x80 pitch)
BOX_X_MIN = 102          # Penalty area starts at 18 yards from goal
BOX_Y_MIN = 18           # Penalty area top
BOX_Y_MAX = 62           # Penalty area bottom
FINAL_THIRD_X = 80       # Final third starts at x=80

# Cut-inside detection
WIDE_RIGHT_Y_MIN = 60    # Right touchline area
WIDE_LEFT_Y_MAX = 20     # Left touchline area
CENTRAL_Y_MIN = 25       # Half-space / center start
CENTRAL_Y_MAX = 55       # Half-space / center end


# ==================================================================================================
# HELPERS
# ==================================================================================================

def _zone(x, y):
    """Returns just the zone number as a string."""
    z = xy_to_zone(x, y)
    return z.split("_")[-1]


def _body(data):
    """Extracts body part abbreviation from a StatsBomb sub-dict."""
    b = data.get("body_part", {}).get("name", "").lower()
    if "right" in b:  return "r"
    if "left"  in b:  return "l"
    if "head"  in b:  return "h"
    return "o"


def _height(data):
    """Extracts pass height abbreviation."""
    h = data.get("height", {}).get("name", "").lower()
    if "ground" in h: return "g"
    if "low"    in h: return "l"
    if "high"   in h: return "h"
    return "g"


def _length_bin(length):
    """Bins pass length into short / medium / long."""
    if length is None:   return "short"
    if length < 10:      return "short"
    if length < 30:      return "med"
    return "long"


# ==================================================================================================
# V2 NEW: SPATIAL HELPERS FOR SEMANTIC TOKENS
# ==================================================================================================

def _is_in_box(x, y):
    """True if (x, y) is in the penalty area."""
    return x > BOX_X_MIN and BOX_Y_MIN <= y <= BOX_Y_MAX


def _is_in_final_third(x):
    """True if x is in the final third."""
    return x > FINAL_THIRD_X


def _is_wide_right(y):
    """True if y is on the right touchline area."""
    return y > WIDE_RIGHT_Y_MIN


def _is_wide_left(y):
    """True if y is on the left touchline area."""
    return y < WIDE_LEFT_Y_MAX


def _is_central(y):
    """True if y is in central / half-space area."""
    return CENTRAL_Y_MIN <= y <= CENTRAL_Y_MAX


def _detect_cut_inside(start_x, start_y, end_x, end_y):
    """
    Detect cut-inside behavior (inverted winger signature).
    Returns: 'cut_inside_right', 'cut_inside_left', or None
    """
    # Must move forward to count as cut-inside
    if end_x <= start_x:
        return None

    # Right side cut inside
    if _is_wide_right(start_y) and _is_central(end_y):
        return "cut_inside_right"

    # Left side cut inside
    if _is_wide_left(start_y) and _is_central(end_y):
        return "cut_inside_left"

    return None


# ==================================================================================================
# MAIN ENTRY POINT
# ==================================================================================================

def event_to_tokens(ev):
    ev_type = ev.get("type", {}).get("name", "").lower()

    if   ev_type == "pass":           return tokenize_pass(ev)
    elif ev_type == "carry":          return tokenize_carry(ev)
    elif ev_type == "dribble":        return tokenize_dribble(ev)
    elif ev_type == "shot":           return tokenize_shot(ev)
    elif ev_type == "duel":           return tokenize_duel(ev)
    elif ev_type == "interception":   return tokenize_interception(ev)
    elif ev_type == "ball recovery":  return tokenize_ball_recovery(ev)
    elif ev_type == "clearance":      return tokenize_clearance(ev)
    elif ev_type == "foul committed": return tokenize_foul_committed(ev)
    elif ev_type == "pressure":       return tokenize_pressure(ev)
    elif ev_type == "block":          return tokenize_block(ev)
    elif ev_type == "dribbled past":  return tokenize_dribbled_past(ev)
    elif ev_type == "dispossessed":   return tokenize_dispossessed(ev)
    else:
        return []


# ==================================================================================================
# PASS (V2 — added to_box, to_final_third, key_pass, assist)
# ==================================================================================================

def tokenize_pass(ev):
    """
    Base token:  pass|z{start}_z{end}|{outcome}|{body}|{height}|{length}
    Example:     pass|z9_z7|s|r|g|short

    Rare modifiers:
        progressive_pass, cross, through_ball, switch, cutback, under_pressure
        [V2 NEW] pass_to_box, pass_to_final_third, key_pass, assist
    """
    if not ev.get("location") or not ev.get("pass"):
        return ["pass|unknown"]

    start_loc = ev["location"]
    end_loc   = ev["pass"].get("end_location")

    if not end_loc:
        return ["pass|unknown"]

    start_x, start_y = start_loc
    end_x,   end_y   = end_loc

    sz      = _zone(start_x, start_y)
    ez      = _zone(end_x, end_y)
    outcome = "s" if ev["pass"].get("outcome") is None else "f"
    body    = _body(ev["pass"])
    height  = _height(ev["pass"])
    length  = _length_bin(ev["pass"].get("length"))

    base = f"pass|z{sz}_z{ez}|{outcome}|{body}|{height}|{length}"
    tokens = [base]

    # --- Existing rare modifiers ---
    if (end_x - start_x) >= PASS_PROGRESSIVE_THRESHOLD:
        tokens.append("progressive_pass")

    if ev["pass"].get("cross"):
        tokens.append("cross")

    if ev["pass"].get("through_ball"):
        tokens.append("through_ball")

    if ev["pass"].get("switch"):
        tokens.append("switch")

    if ev["pass"].get("cut_back"):
        tokens.append("cutback")

    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    # --- V2 NEW: Spatial destination modifiers (only for successful passes) ---
    if outcome == "s":
        if _is_in_box(end_x, end_y):
            tokens.append("pass_to_box")
        elif _is_in_final_third(end_x) and not _is_in_final_third(start_x):
            tokens.append("pass_to_final_third")

    # --- V2 NEW: Quality modifiers (key_pass, assist) ---
    if ev["pass"].get("shot_assist"):
        tokens.append("key_pass")

    if ev["pass"].get("goal_assist"):
        tokens.append("assist")

    return tokens


# ==================================================================================================
# CARRY (V2 — added cut_inside, to_box, to_final_third)
# ==================================================================================================

def tokenize_carry(ev):
    """
    Base token:  carry|z{start}_z{end}|{direction}
    Example:     carry|z9_z13|fwd

    Rare modifiers:
        progressive_carry, under_pressure
        [V2 NEW] cut_inside_right, cut_inside_left, carry_to_box, carry_to_final_third
    """
    start = ev.get("location")
    end   = ev.get("carry", {}).get("end_location")

    if not start or not end:
        return ["carry|unknown"]

    sx, sy = start
    ex, ey = end

    sz  = _zone(sx, sy)
    ez  = _zone(ex, ey)
    dx  = ex - sx

    if   dx > 5:  direction = "fwd"
    elif dx < -5: direction = "bwd"
    else:         direction = "lat"

    base = f"carry|z{sz}_z{ez}|{direction}"
    tokens = [base]

    # --- Existing rare modifiers ---
    if dx >= CARRY_PROGRESSIVE_THRESHOLD:
        tokens.append("progressive_carry")

    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    # --- V2 NEW: Cut-inside detection (Mané/Salah signature) ---
    cut_inside = _detect_cut_inside(sx, sy, ex, ey)
    if cut_inside:
        tokens.append(cut_inside)

    # --- V2 NEW: Spatial destination modifiers ---
    if _is_in_box(ex, ey):
        tokens.append("carry_to_box")
    elif _is_in_final_third(ex) and not _is_in_final_third(sx):
        tokens.append("carry_to_final_third")

    return tokens


# ==================================================================================================
# DRIBBLE (V2 — added wide-area + in-box modifiers)
# ==================================================================================================

def tokenize_dribble(ev):
    """
    Base token:  dribble|z{zone}|{outcome}
    Example:     dribble|z9|s

    Rare modifiers:
        under_pressure
        [V2 NEW] dribble_right_wide, dribble_left_wide, dribble_in_box
    """
    loc = ev.get("location")
    if not loc:
        return ["dribble|unknown"]

    x, y    = loc
    z       = _zone(x, y)
    outcome = ev.get("dribble", {}).get("outcome", {}).get("name", "").lower()
    o       = "s" if "complete" in outcome else "f"

    base   = f"dribble|z{z}|{o}"
    tokens = [base]

    # --- Existing modifier ---
    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    # --- V2 NEW: Spatial context for dribbles ---
    if _is_wide_right(y):
        tokens.append("dribble_right_wide")
    elif _is_wide_left(y):
        tokens.append("dribble_left_wide")

    if _is_in_box(x, y):
        tokens.append("dribble_in_box")

    return tokens


# ==================================================================================================
# SHOT (unchanged from V1 — already excellent)
# ==================================================================================================

def tokenize_shot(ev):
    """
    Base token:  shot|z{zone}|{outcome}|{body}|{type}|{xg_bin}|{dist_bin}
    Example:     shot|z15|goal|r|open|xg_h|close
    """
    shot = ev.get("shot", {})
    loc  = ev.get("location")

    if not loc:
        return ["shot|unknown"]

    x, y = loc
    z    = _zone(x, y)

    outcome_str = shot.get("outcome", {}).get("name", "").lower()
    if "goal"  in outcome_str:                            o = "goal"
    elif "saved" in outcome_str or "post" in outcome_str: o = "on"
    else:                                                  o = "off"

    body = _body(shot)

    shot_type = shot.get("type", {}).get("name", "").lower()
    if   "open play" in shot_type: t = "open"
    elif "penalty"   in shot_type: t = "pen"
    else:                          t = "set"

    xg = shot.get("statsbomb_xg")
    if   xg is None:  xg_bin = "xg_u"
    elif xg < 0.1:    xg_bin = "xg_l"
    elif xg < 0.3:    xg_bin = "xg_m"
    else:             xg_bin = "xg_h"

    dist = ((120 - x) ** 2 + (40 - y) ** 2) ** 0.5
    if   dist < 10: dist_bin = "close"
    elif dist < 20: dist_bin = "mid"
    else:           dist_bin = "long"

    base   = f"shot|z{z}|{o}|{body}|{t}|{xg_bin}|{dist_bin}"
    tokens = [base]

    if shot.get("one_on_one"):  tokens.append("one_on_one")
    if shot.get("open_goal"):   tokens.append("open_goal")
    if shot.get("first_time"):  tokens.append("first_time")

    return tokens


# ==================================================================================================
# DUEL (unchanged)
# ==================================================================================================

def tokenize_duel(ev):
    duel = ev.get("duel", {})
    loc  = ev.get("location")

    if not loc:
        return ["duel|unknown"]

    x, y = loc
    z    = _zone(x, y)

    duel_type = duel.get("type", {}).get("name", "").lower()
    t = "aerial" if "aerial" in duel_type else "ground"

    outcome = duel.get("outcome", {}).get("name", "").lower()
    o = "won" if "won" in outcome else "lost"

    base   = f"duel|z{z}|{t}|{o}"
    tokens = [base]

    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ==================================================================================================
# INTERCEPTION (unchanged)
# ==================================================================================================

def tokenize_interception(ev):
    loc = ev.get("location")
    if not loc:
        return ["interception|unknown"]

    x, y    = loc
    z       = _zone(x, y)
    outcome = ev.get("interception", {}).get("outcome", {}).get("name", "").lower()
    o       = "won" if "won" in outcome else "lost"

    base   = f"interception|z{z}|{o}"
    tokens = [base]

    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ==================================================================================================
# BALL RECOVERY (unchanged)
# ==================================================================================================

def tokenize_ball_recovery(ev):
    loc = ev.get("location")
    if not loc:
        return ["ball_recovery|unknown"]

    x, y = loc
    z    = _zone(x, y)
    o    = "f" if ev.get("ball_recovery", {}).get("recovery_failure") else "s"

    base   = f"ball_recovery|z{z}|{o}"
    tokens = [base]

    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ==================================================================================================
# CLEARANCE (unchanged)
# ==================================================================================================

def tokenize_clearance(ev):
    loc = ev.get("location")
    if not loc:
        return ["clearance|unknown"]

    x, y = loc
    z    = _zone(x, y)
    body = _body(ev.get("clearance", {}))

    base   = f"clearance|z{z}|{body}"
    tokens = [base]

    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ==================================================================================================
# FOUL COMMITTED (unchanged)
# ==================================================================================================

def tokenize_foul_committed(ev):
    loc = ev.get("location")
    if not loc:
        return ["foul_committed|unknown"]

    x, y = loc
    z    = _zone(x, y)

    card = ev.get("foul_committed", {}).get("card", {}).get("name", "").lower()
    if   "yellow" in card: card_token = "yellow"
    elif "red"    in card: card_token = "red"
    else:                  card_token = "none"

    base   = f"foul_committed|z{z}|{card_token}"
    tokens = [base]

    if ev.get("foul_committed", {}).get("penalty"):
        tokens.append("foul_penalty")

    return tokens


# ==================================================================================================
# PRESSURE (V2 — counterpress now part of base token)
# ==================================================================================================

def tokenize_pressure(ev):
    """
    Base token: pressure|z{zone}|{cp_or_reg}
    Examples:
        pressure|z21|cp     (counterpress — Klopp's gegenpressing signature)
        pressure|z21|reg    (regular pressure)

    Counterpress is encoded in base token (not as rare modifier) because
    it's a fundamental quality distinction we want the model to learn.
    """
    loc = ev.get("location")
    if not loc:
        return ["pressure|unknown"]
    x, y = loc
    z = _zone(x, y)

    cp = "cp" if ev.get("counterpress") else "reg"

    return [f"pressure|z{z}|{cp}"]


# ==================================================================================================
# BLOCK (unchanged)
# ==================================================================================================

def tokenize_block(ev):
    loc = ev.get("location")
    if not loc:
        return ["block|unknown"]
    x, y = loc
    z = _zone(x, y)
    deflection = "def" if ev.get("block", {}).get("deflection") else "blk"
    return [f"block|z{z}|{deflection}"]


# ==================================================================================================
# DRIBBLED PAST (unchanged)
# ==================================================================================================

def tokenize_dribbled_past(ev):
    loc = ev.get("location")
    if not loc:
        return ["dribbled_past|unknown"]
    x, y = loc
    z = _zone(x, y)
    return [f"dribbled_past|z{z}"]


# ==================================================================================================
# DISPOSSESSED (unchanged)
# ==================================================================================================

def tokenize_dispossessed(ev):
    loc = ev.get("location")
    if not loc:
        return ["dispossessed|unknown"]
    x, y = loc
    z = _zone(x, y)
    return [f"dispossessed|z{z}"]