import os
import json
from collections import defaultdict, Counter
from tqdm import tqdm

DATA_DIR = "data"
OUT_DIR = "models/gp1/shared/event_analysis"

os.makedirs(OUT_DIR, exist_ok=True)


def load_match(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("🔍 Scanning StatsBomb events...")

    event_types = Counter()
    positions = Counter()

    # nested attributes
    attribute_keys = defaultdict(set)
    attribute_values = defaultdict(set)

    # specific tracking
    pass_attrs = defaultdict(set)
    shot_attrs = defaultdict(set)
    carry_attrs = defaultdict(set)
    dribble_attrs = defaultdict(set)
    duel_attrs = defaultdict(set)

    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]

    for file in tqdm(files):
        match = load_match(os.path.join(DATA_DIR, file))

        for ev in match:
            # =========================
            # Event Type
            # =========================
            if "type" in ev and ev["type"]:
                etype = ev["type"]["name"]
                event_types[etype] += 1

            # =========================
            # Player Position
            # =========================
            if "position" in ev and ev["position"]:
                pos = ev["position"]["name"]
                positions[pos] += 1

            # =========================
            # Generic attributes scan
            # =========================
            for key, val in ev.items():
                if isinstance(val, dict):
                    attribute_keys[key].update(val.keys())

                    for sub_k, sub_v in val.items():
                        if isinstance(sub_v, dict) and "name" in sub_v:
                            attribute_values[f"{key}.{sub_k}"].add(sub_v["name"])

                        elif isinstance(sub_v, list):
                            continue

                        else:
                            attribute_values[f"{key}.{sub_k}"].add(str(sub_v))

            # =========================
            # Specific event breakdown
            # =========================
            if "pass" in ev:
                for k, v in ev["pass"].items():
                    if isinstance(v, dict) and "name" in v:
                        pass_attrs[k].add(v["name"])
                    else:
                        pass_attrs[k].add(str(v))

            if "shot" in ev:
                for k, v in ev["shot"].items():
                    if isinstance(v, dict) and "name" in v:
                        shot_attrs[k].add(v["name"])
                    else:
                        shot_attrs[k].add(str(v))

            if "carry" in ev:
                for k, v in ev["carry"].items():
                    carry_attrs[k].add(str(v))

            if "dribble" in ev:
                for k, v in ev["dribble"].items():
                    if isinstance(v, dict) and "name" in v:
                        dribble_attrs[k].add(v["name"])
                    else:
                        dribble_attrs[k].add(str(v))

            if "duel" in ev:
                for k, v in ev["duel"].items():
                    if isinstance(v, dict) and "name" in v:
                        duel_attrs[k].add(v["name"])
                    else:
                        duel_attrs[k].add(str(v))

    print("✅ Done scanning")

    # =========================
    # Save results
    # =========================

    def save(obj, name):
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)

    save(dict(event_types), "event_types.json")
    save(dict(positions), "positions.json")
    save({k: list(v) for k, v in attribute_keys.items()}, "attribute_keys.json")
    save({k: list(v) for k, v in attribute_values.items()}, "attribute_values.json")

    save({k: list(v) for k, v in pass_attrs.items()}, "pass_attributes.json")
    save({k: list(v) for k, v in shot_attrs.items()}, "shot_attributes.json")
    save({k: list(v) for k, v in carry_attrs.items()}, "carry_attributes.json")
    save({k: list(v) for k, v in dribble_attrs.items()}, "dribble_attributes.json")
    save({k: list(v) for k, v in duel_attrs.items()}, "duel_attributes.json")

    print(f"📁 Results saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()