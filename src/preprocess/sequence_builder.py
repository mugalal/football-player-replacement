def build_possession_sequences(events, event_to_tokens):
    sequences = []

    current_sequence = []
    current_key = None  # (possession_id, team_id)

    for ev in events:
        # --- extract possession info ---
        possession_id = ev.get("possession")
        team_id = ev.get("possession_team", {}).get("id")

        # skip if missing (rare but safe)
        if possession_id is None or team_id is None:
            continue

        key = (possession_id, team_id)

        # --- new possession starts ---
        if key != current_key:
            if current_sequence:
                sequences.append(current_sequence)

            current_sequence = []
            current_key = key

        # --- tokenize event ---
        tokens = event_to_tokens(ev)

        player_id = ev.get("player", {}).get("id")

        if tokens and player_id is not None:
            current_sequence.append({
                "player_id": player_id,
                "tokens": tokens
            })

    # --- last sequence ---
    if current_sequence:
        sequences.append(current_sequence)

    return sequences