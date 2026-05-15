from src.model.transformer import FootballTransformer
import torch

model = FootballTransformer(vocab_size=110)

x = torch.randint(0, 110, (4, 50))  # batch of 4, seq_len=50

out = model(x)

print(out.shape)