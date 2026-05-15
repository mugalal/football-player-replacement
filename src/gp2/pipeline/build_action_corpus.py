import json

from src.gp2.preprocess.tokens import event_to_tokens
from src.gp2.preprocess.sequence_builder import build_possession_sequences
from src.gp2.preprocess.prepare_sequences import flatten_sequences, filter_sequences_by_length
from src.gp2.paths import ACTION_SENTENCES_PATH, FULL_MATCHES_DIR


def main():
    print("Building Action2Vec corpus (streaming mode)...")

    ACTION_SENTENCES_PATH.parent.mkdir(parents=True, exist_ok=True)

    total_sequences = 0

    with open(ACTION_SENTENCES_PATH, "w", encoding="utf-8") as out_f:

        for i, file in enumerate(FULL_MATCHES_DIR.glob("*.json")):
            match_id = file.stem

            with open(file, "r", encoding="utf-8") as f:
                events = json.load(f)

                # inject match_id
                for ev in events:
                    ev["match_id"] = match_id

            # process this match only
            sequences = build_possession_sequences(events, event_to_tokens)
            flat_sequences = flatten_sequences(sequences)
            flat_sequences = filter_sequences_by_length(flat_sequences, min_len=10, max_len=200)

            # save immediately
            for seq in flat_sequences:
                out_f.write(json.dumps(seq) + "\n")

            total_sequences += len(flat_sequences)

            # progress log every 50 matches
            if i % 50 == 0:
                print(f"Processed {i} matches | total sequences: {total_sequences}")

    print("✅ Done")
    print(f"Total sequences: {total_sequences}")


if __name__ == "__main__":
    main()
