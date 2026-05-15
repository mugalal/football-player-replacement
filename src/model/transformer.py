import torch
import torch.nn as nn

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=500):
        super().__init__()

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1)

        div_term = torch.exp(
            torch.arange(0, d_model, 2) * (-torch.log(torch.tensor(10000.0)) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        self.pe = pe.unsqueeze(0)  # (1, max_len, d_model)

    def forward(self, x):
        return x + self.pe[:, :x.size(1)].to(x.device)

class FootballTransformer(nn.Module):
    def __init__(
        self,
        vocab_size,
        d_model=128,
        n_heads=4,
        n_layers=2,
        dim_feedforward=256,
        max_len=200,
        dropout=0.1,
    ):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model, max_len)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True  # IMPORTANT
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers
        )

        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        # x: (B, L)

        mask = (x == 0)

        x = self.embedding(x)        # (B, L, D)
        x = self.pos_encoding(x)     # (B, L, D)

        x = self.transformer(
            x,
            src_key_padding_mask=mask
        )                            # (B, L, D)

        logits = self.fc_out(x)

        return logits
    
    def get_embeddings(self, x):
        """
        x: (B, L)
        returns: (B, D)
        """
        mask = (x == 0)  # (B, L)

        x = self.embedding(x)        # (B, L, D)
        x = self.pos_encoding(x)     # (B, L, D)

        # 🚀 NO TRANSPOSE HERE
        x = self.transformer(
            x,
            src_key_padding_mask=mask
        )  # (B, L, D)

        # 🔥 mean pooling (ignore padding)
        valid_mask = (~mask).unsqueeze(-1)

        x = x * valid_mask
        summed = x.sum(dim=1)
        counts = valid_mask.sum(dim=1)

        embeddings = summed / counts.clamp(min=1)

        return embeddings  # (B, D)
    
      

