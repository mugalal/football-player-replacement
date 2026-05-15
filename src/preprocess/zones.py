"""
zones.py
--------

Handles conversion between (x, y) coordinates and pitch zones.

StatsBomb pitch:
    x ∈ [0, 120]
    y ∈ [0, 80]
"""

# =====================
# CONFIG
# =====================

PITCH_LENGTH = 120.0
PITCH_WIDTH  = 80.0

NUM_X_BINS = 6   # horizontal divisions
NUM_Y_BINS = 3   # vertical divisions


# =====================
# CORE FUNCTIONS
# =====================

def xy_to_zone(x, y, num_x=NUM_X_BINS, num_y=NUM_Y_BINS):
    """
    Convert (x, y) → zone_id

    Zones are indexed row-wise:
        zone_0 ... zone_(num_x*num_y - 1)

    Example (6x3):
        zone_0 zone_1 zone_2 ...
    """
    if x is None or y is None:
        return "zone_unknown"

    # Clamp values
    x = max(0.0, min(PITCH_LENGTH, float(x)))
    y = max(0.0, min(PITCH_WIDTH, float(y)))

    bx = min(int((x / PITCH_LENGTH) * num_x), num_x - 1)
    by = min(int((y / PITCH_WIDTH) * num_y), num_y - 1)

    return f"{by * num_x + bx}"


def get_start_zone(ev):
    """
    Extract start zone from event
    """
    loc = ev.get("location")
    if not loc:
        return "zone_unknown"

    return xy_to_zone(loc[0], loc[1])


def get_end_zone(ev):
    """
    Extract end zone depending on event type
    """
    ev_type = ev.get("type", {}).get("name", "").lower()

    if ev_type == "pass":
        end = ev.get("pass", {}).get("end_location")

    elif ev_type == "carry":
        end = ev.get("carry", {}).get("end_location")

    elif ev_type == "shot":
        end = ev.get("shot", {}).get("end_location")

    else:
        return "zone_unknown"

    if not end:
        return "zone_unknown"

    return xy_to_zone(end[0], end[1])


# =====================
# OPTIONAL UTILITIES
# =====================

def zone_center(zone_id, num_x=NUM_X_BINS, num_y=NUM_Y_BINS):
    """
    Convert zone_id → approximate (x, y) center
    Useful for distance / progressive logic later
    """
    if not zone_id.startswith("zone_"):
        return None, None

    zid = int(zone_id.split("_")[1])

    bx = zid % num_x
    by = zid // num_x

    x = (bx + 0.5) * (PITCH_LENGTH / num_x)
    y = (by + 0.5) * (PITCH_WIDTH / num_y)

    return x, y


def zone_distance(z1, z2):
    """
    Euclidean distance between two zones (center-based)
    """
    x1, y1 = zone_center(z1)
    x2, y2 = zone_center(z2)

    if x1 is None or x2 is None:
        return 0.0

    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5