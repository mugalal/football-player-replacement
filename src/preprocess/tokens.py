from .zones import xy_to_zone


# ==================================================================================================
# CONFIG
# ==================================================================================================

PASS_PROGRESSIVE_THRESHOLD = 10
CARRY_PROGRESSIVE_THRESHOLD = 10


# ==================================================================================================
# DESIGN PHILOSOPHY
# ==================================================================================================
#
# Each event produces:
#   1. ONE composite base token  — encodes the full identity of the action
#      Format: "event_type|key_attribute_1|key_attribute_2|..."
#      Example: "pass|z9_z7|s|r|g|short"
#                         ↑     ↑ ↑ ↑ ↑
#              zones   outcome body height length
#
#   2. ZERO or MORE rare modifier tokens — only emitted when truly present
#      These are kept separate because they carry meaning in SEQUENCE CONTEXT:
#      e.g. "cross → shot" is a real pattern Word2Vec should learn.
#      If merged into the base token they'd appear too rarely to learn embeddings.
#
# WHY composite base tokens?
#   With atomic tokens (old design), Word2Vec window=3 was consumed by attributes
#   of the SAME event (body_right, pass_short, pass_ground all for one pass).
#   The model learned attribute co-occurrence within events, not transitions between events.
#   With one composite token per event, window=3 always spans 3 actual football actions.
#
# VOCAB GROWTH:
#   25 zones × 25 zones × 2 outcomes × 3 body parts × 3 heights × 3 lengths
#   → ~10,000+ unique pass tokens alone (Magdaci's ~19K becomes achievable)
#
# ==================================================================================================


# ==================================================================================================
# HELPERS
# ==================================================================================================

def _zone(x, y):
    """
    Returns just the zone number as a string (e.g. "9") by stripping
    the "zone_" prefix that xy_to_zone returns.
    This keeps composite tokens readable: "pass|z9_z7|..." not "pass|zone_9_zone_7|..."
    """
    z = xy_to_zone(x, y)           # returns "zone_9"
    return z.split("_")[-1]        # returns "9"


def _body(data):
    """Extracts body part abbreviation from a StatsBomb sub-dict."""
    b = data.get("body_part", {}).get("name", "").lower()
    if "right" in b:  return "r"
    if "left"  in b:  return "l"
    if "head"  in b:  return "h"
    return "o"                      # other (chest, no touch, etc.)


def _height(data):
    """Extracts pass height abbreviation."""
    h = data.get("height", {}).get("name", "").lower()
    if "ground" in h: return "g"
    if "low"    in h: return "l"
    if "high"   in h: return "h"
    return "g"                      # default ground if missing


def _length_bin(length):
    """Bins pass length into short / medium / long."""
    if length is None:   return "short"
    if length < 10:      return "short"
    if length < 30:      return "med"
    return "long"


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
    else:
        return []


# ==================================================================================================
# TOKENIZATION FUNCTIONS
# ==================================================================================================

# ================================
# PASS
# ================================

def tokenize_pass(ev):
    """
    Base token:  pass|z{start}_z{end}|{outcome}|{body}|{height}|{length}
    Example:     pass|z9_z7|s|r|g|short
                                   ↑ success, right foot, ground pass, short

    Rare modifiers (kept separate for sequence context learning):
        progressive_pass, cross, through_ball, switch, cutback, under_pressure
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

    # --- Rare modifiers ---
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

    return tokens


# ================================
# CARRY
# ================================

def tokenize_carry(ev):
    """
    Base token:  carry|z{start}_z{end}|{direction}
    Example:     carry|z9_z13|fwd

    Direction: fwd (forward), bwd (backward), lat (lateral)

    Rare modifiers: progressive_carry, under_pressure
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

    # --- Rare modifiers ---
    if dx >= CARRY_PROGRESSIVE_THRESHOLD:
        tokens.append("progressive_carry")

    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ================================
# DRIBBLE
# ================================

def tokenize_dribble(ev):
    """
    Base token:  dribble|z{zone}|{outcome}
    Example:     dribble|z9|s

    Rare modifiers: under_pressure
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

    # --- Rare modifiers ---
    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ================================
# SHOT
# ================================

def tokenize_shot(ev):
    """
    Base token:  shot|z{zone}|{outcome}|{body}|{type}|{xg_bin}|{dist_bin}
    Example:     shot|z15|goal|r|open|xg_h|close

    outcome: goal / on (on target) / off (off target)
    type:    open / pen (penalty) / set (set piece)
    xg_bin:  xg_l (<0.1) / xg_m (<0.3) / xg_h (>=0.3)
    dist:    close (<10m) / mid (<20m) / long (>=20m)

    Rare modifiers: one_on_one, open_goal, first_time
    """
    shot = ev.get("shot", {})
    loc  = ev.get("location")

    if not loc:
        return ["shot|unknown"]

    x, y = loc
    z    = _zone(x, y)

    # outcome
    outcome_str = shot.get("outcome", {}).get("name", "").lower()
    if "goal"  in outcome_str:                          o = "goal"
    elif "saved" in outcome_str or "post" in outcome_str: o = "on"
    else:                                                   o = "off"

    body = _body(shot)

    # shot type
    shot_type = shot.get("type", {}).get("name", "").lower()
    if   "open play" in shot_type: t = "open"
    elif "penalty"   in shot_type: t = "pen"
    else:                          t = "set"

    # xG bin
    xg = shot.get("statsbomb_xg")
    if   xg is None:  xg_bin = "xg_u"   # unknown
    elif xg < 0.1:    xg_bin = "xg_l"
    elif xg < 0.3:    xg_bin = "xg_m"
    else:             xg_bin = "xg_h"

    # distance to goal (goal centre at 120, 40)
    dist = ((120 - x) ** 2 + (40 - y) ** 2) ** 0.5
    if   dist < 10: dist_bin = "close"
    elif dist < 20: dist_bin = "mid"
    else:           dist_bin = "long"

    base   = f"shot|z{z}|{o}|{body}|{t}|{xg_bin}|{dist_bin}"
    tokens = [base]

    # --- Rare modifiers ---
    if shot.get("one_on_one"):  tokens.append("one_on_one")
    if shot.get("open_goal"):   tokens.append("open_goal")
    if shot.get("first_time"):  tokens.append("first_time")

    return tokens


# ================================
# DUEL
# ================================

def tokenize_duel(ev):
    """
    Base token:  duel|z{zone}|{type}|{outcome}
    Example:     duel|z9|ground|won

    Rare modifiers: under_pressure
    """
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

    # --- Rare modifiers ---
    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ================================
# INTERCEPTION
# ================================

def tokenize_interception(ev):
    """
    Base token:  interception|z{zone}|{outcome}
    Example:     interception|z5|won

    Rare modifiers: under_pressure
    """
    loc = ev.get("location")
    if not loc:
        return ["interception|unknown"]

    x, y    = loc
    z       = _zone(x, y)
    outcome = ev.get("interception", {}).get("outcome", {}).get("name", "").lower()
    o       = "won" if "won" in outcome else "lost"

    base   = f"interception|z{z}|{o}"
    tokens = [base]

    # --- Rare modifiers ---
    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ================================
# BALL RECOVERY
# ================================

def tokenize_ball_recovery(ev):
    """
    Base token:  ball_recovery|z{zone}|{outcome}
    Example:     ball_recovery|z3|s

    Rare modifiers: under_pressure
    """
    loc = ev.get("location")
    if not loc:
        return ["ball_recovery|unknown"]

    x, y = loc
    z    = _zone(x, y)
    o    = "f" if ev.get("ball_recovery", {}).get("recovery_failure") else "s"

    base   = f"ball_recovery|z{z}|{o}"
    tokens = [base]

    # --- Rare modifiers ---
    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens


# ================================
# CLEARANCE
# ================================

def tokenize_clearance(ev):
    """
    Base token:  clearance|z{zone}|{body}
    Example:     clearance|z3|h

    Rare modifiers: under_pressure
    """
    loc = ev.get("location")
    if not loc:
        return ["clearance|unknown"]

    x, y = loc
    z    = _zone(x, y)
    body = _body(ev.get("clearance", {}))

    base   = f"clearance|z{z}|{body}"
    tokens = [base]

    # --- Rare modifiers ---
    if ev.get("under_pressure"):
        tokens.append("under_pressure")

    return tokens