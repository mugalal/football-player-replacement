import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from src.model.transformer import FootballTransformer


def mask_tokens(inputs, vocab_size, mask_token_id=2, pad_token_id=0, mask_prob=0.2):
    inputs = inputs.clone()  
    labels = inputs.clone()

    probability_matrix = torch.full(labels.shape, mask_prob)

    special_mask = inputs.eq(pad_token_id)
    probability_matrix.masked_fill_(special_mask, value=0.0)

    mask = torch.bernoulli(probability_matrix).bool()

    labels[~mask] = -100  # ignore non-masked tokens

    # 80% replace with MASK
    indices_replaced = torch.bernoulli(torch.full(labels.shape, 0.8)).bool() & mask
    inputs[indices_replaced] = mask_token_id

    # 10% random token
    indices_random = torch.bernoulli(torch.full(labels.shape, 0.5)).bool() & mask & ~indices_replaced
    random_tokens = torch.randint(vocab_size, labels.shape, dtype=torch.long)
    inputs[indices_random] = random_tokens[indices_random]

    # 10% unchanged

    return inputs, labels
    
def train_model(padded_sequences, vocab_size, epochs=5, lr=1e-3):
    device = torch.device("cpu")
    print("Using device:", device)

    # Model
    model = FootballTransformer(vocab_size=vocab_size).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    criterion = nn.CrossEntropyLoss(ignore_index=-100)

    # Data
    data = torch.tensor(padded_sequences, dtype=torch.long)
    dataset = TensorDataset(data)

    # 🔥 Train / Validation split
    val_size = int(0.1 * len(dataset))
    train_size = len(dataset) - val_size
    torch.manual_seed(42)
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64)

    # Training loop
    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for batch in train_loader:
            batch = batch[0].to(device)

            # 🔥 Masked LM (no clone needed now)
            inputs, labels = mask_tokens(batch, vocab_size)

            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)

            outputs = outputs.reshape(-1, vocab_size)
            labels = labels.reshape(-1)

            loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()

            # 🔥 Prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            optimizer.step()

            total_loss += loss.item()

        # 🔥 Validation
        model.eval()
        val_loss = 0

        with torch.no_grad():
            for batch in val_loader:
                batch = batch[0].to(device)

                inputs, labels = mask_tokens(batch, vocab_size)

                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)

                outputs = outputs.reshape(-1, vocab_size)
                labels = labels.reshape(-1)

                loss = criterion(outputs, labels)
                val_loss += loss.item()

        scheduler.step()

        print(
            f"Epoch {epoch+1}/{epochs} | "
            f"Train Loss: {total_loss / len(train_loader):.4f} | "
            f"Val Loss: {val_loss / len(val_loader):.4f}"
        )

    # 🔥 Save model
    torch.save(model.state_dict(), "football_transformer.pt")

    return model

def load_model(path, vocab_size, device):
    model = FootballTransformer(vocab_size=vocab_size).to(device)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()
    return model
