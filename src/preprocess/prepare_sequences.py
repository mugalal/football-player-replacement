def flatten_sequences(sequences):
    flat_sequences = []
    player_ids = []

    for seq in sequences:
        flat_seq = []
        seq_players = []

        for event in seq:
            flat_seq.extend(event["tokens"])
            seq_players.append(event["player_id"])

        flat_sequences.append(flat_seq)
        player_ids.append(seq_players)

    return flat_sequences, player_ids

def build_vocab(sequences, min_freq=1):
    from collections import Counter

    counter = Counter()

    for seq in sequences:
        counter.update(seq)

    vocab = {
        "<PAD>": 0,
        "<UNK>": 1,
        "<MASK>": 2,
    }

    idx = 3

    for token, freq in counter.items():
        if freq >= min_freq:
            vocab[token] = idx
            idx += 1

    return vocab

def encode_sequences(sequences, vocab):
    encoded = []

    for seq in sequences:
        encoded_seq = [
            vocab.get(token, vocab["<UNK>"])
            for token in seq
        ]
        encoded.append(encoded_seq)

    return encoded

def pad_sequences(sequences, max_len=100):
    padded = []

    for seq in sequences:
        # 1. CLIP first
        if len(seq) > max_len:
            seq = seq[:max_len]

        # 2. PAD after
        if len(seq) < max_len:
            seq = seq + [0] * (max_len - len(seq))  # PAD = 0

        padded.append(seq)

    return padded