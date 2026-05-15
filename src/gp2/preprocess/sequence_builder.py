def build_possession_sequences(events, event_to_tokens , min_seq_len=10):
    sequences = []

    current_tokens = []
    current_events = []
    current_key = None  # (possession_id, team_id)
    current_period = None

    for ev in events:
        possession_id = ev.get("possession")
        team_id = ev.get("possession_team", {}).get("id")
        period = ev.get("period")

        if possession_id is None or team_id is None:
            continue

        key = (possession_id, team_id)

        event_team_id = ev.get("team", {}).get("id")

        if event_team_id != team_id:   # team_id is possession_team id
            continue                    # skip defending team's actions from possession sentence

        current_period = period

        # New possession
        if key != current_key:
            if current_tokens:
                sequences.append({
                    "tokens": current_tokens,
                    "events": current_events,
                    "period": current_period
                })

            current_tokens = []
            current_events = []
            current_key = key

        tokens = event_to_tokens(ev)

        if tokens:
            current_tokens.extend(tokens)
            current_events.append(ev)
            

    # Last sequence
    if current_tokens:
        sequences.append({
            "tokens": current_tokens,
            "events": current_events,
            "period": current_period
        })

    merged = []
    buffer_tokens = []
    buffer_events = []
    prev_period = None

    for seq in sequences:
        if seq["period"] != prev_period and buffer_tokens:
            merged.append({"tokens": buffer_tokens, "events": buffer_events})
            buffer_tokens = []
            buffer_events = []
        prev_period = seq["period"]

        buffer_tokens.extend(seq["tokens"])
        buffer_events.extend(seq["events"])

        if len(buffer_tokens) >= min_seq_len:      
            merged.append({"tokens": buffer_tokens, "events": buffer_events})
            buffer_tokens = []
            buffer_events = []

    if buffer_tokens:
        if merged:
            merged[-1]["tokens"].extend(buffer_tokens)
            merged[-1]["events"].extend(buffer_events)
        else:
            merged.append({"tokens": buffer_tokens, "events": buffer_events})

    return merged  # ← was: return sequences
