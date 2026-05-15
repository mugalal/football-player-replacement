from src.model.similarity import find_similar_players
import torch
import json

def load_player_names(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def get_player_name(pid, player_map):
    return player_map.get(str(pid), f"Unknown ({pid})")    
# Load embeddings
data = torch.load("player_embeddings.pt")
player_embeddings = data["embeddings"]

# Load names
player_map = load_player_names("models/gp1/shared/player_id_to_name.json")

while True:
    try:
        query = input("\nEnter player ID (or 'q' to quit): ")

        if query.lower() == 'q':
            print("Exiting search...")
            break

        query_id = int(query)

    except ValueError:
        print("Invalid input! Please enter a number.")
        continue

    if query_id not in player_embeddings:
        print("Player not found!")
        continue

    # Print query player
    print(f"\n🔎 Query Player:")
    print(f"{query_id} → {get_player_name(query_id, player_map)}")

    # Get similar players
    similar = find_similar_players(query_id, player_embeddings, top_k=5)

    print("\nTop similar players:\n")
    for pid, score in similar:
        name = get_player_name(pid, player_map)
        print(f"{pid} → {name} | similarity: {score:.4f}")