# prepare_sequences.py

def flatten_sequences(sequences):

    flat_sequences = []

    for seq in sequences:
        # NEW FORMAT
        if isinstance(seq, dict):
            tokens = seq["tokens"]
        else:
            # fallback (just in case)
            tokens = seq

        if tokens:
            flat_sequences.append(tokens)

    return flat_sequences  # player_ids not needed for Word2Vec, can be added later for Doc2Vec


def filter_sequences_by_length(sequences, min_len=5, max_len=200):

    filtered = []

    for seq in sequences:
        if min_len <= len(seq) <= max_len:
            filtered.append(seq)

    return filtered