import json

POS_MAP = {}

# Load extracted positions
with open("models/gp1/shared/unique_positions.json", encoding="utf-8") as f:
    positions = json.load(f)

for p in positions:
    name = p.lower()

    if "goalkeeper" in name:
        macro = "GK"

    elif "back" in name:
        macro = "DEF"

    elif "wing back" in name:
        macro = "DEF"

    elif "center back" in name:
        macro = "DEF"

    elif "defensive midfield" in name:
        macro = "MID"

    elif "attacking midfield" in name:
        macro = "MID"

    elif "midfield" in name:
        macro = "MID"

    elif "forward" in name or "wing" in name:
        macro = "ATT"

    elif "substitute" in name:
        macro = "UNKNOWN"

    else:
        macro = "UNKNOWN"

    POS_MAP[p] = macro

with open("models/shared/position_macro_map.json", "w", encoding="utf-8") as f:
    json.dump(POS_MAP, f, ensure_ascii=False, indent=2)

print("Saved to models/shared/position_macro_map.json")
