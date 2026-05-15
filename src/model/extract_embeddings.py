import torch

def extract_embeddings(model, padded_sequences, batch_size=64):
    device = next(model.parameters()).device

    model.eval()

    data = torch.tensor(padded_sequences, dtype=torch.long)
    dataset = torch.utils.data.TensorDataset(data)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size)

    all_embeddings = []

    with torch.no_grad():
        for batch in loader:
            batch = batch[0].to(device)

            emb = model.get_embeddings(batch)  # (B, D)
            all_embeddings.append(emb.cpu())

    return torch.cat(all_embeddings, dim=0)  # (N, D)