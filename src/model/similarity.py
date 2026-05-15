import torch
import torch.nn.functional as F


def cosine_similarity(vec1, vec2):
    return F.cosine_similarity(vec1.unsqueeze(0), vec2.unsqueeze(0)).item()


def find_similar_players(player_id, player_embeddings, top_k=5):
    if player_id not in player_embeddings:
        return []

    target_vec = player_embeddings[player_id]

    ids = [pid for pid in player_embeddings if pid != player_id]
    matrix = torch.stack([player_embeddings[pid] for pid in ids])

    sims = torch.matmul(matrix, target_vec)

    top_k_idx = torch.topk(sims, k=min(top_k, len(ids))).indices

    return [(ids[i], sims[i].item()) for i in top_k_idx]