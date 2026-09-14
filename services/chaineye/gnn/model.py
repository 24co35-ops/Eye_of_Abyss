"""
3-Layer GraphSAGE GNN Model for Crypto Forensics and Wallet Classification.
Trained on Elliptic-style transaction features to classify wallet entities into:
[exchange, mixer, mule, unknown] and attribute specific VASPs.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


if HAS_TORCH:
    class GraphSAGELayer(nn.Module):
        """Standard GraphSAGE Mean Aggregation Layer with self + neighbor linear projections."""

        def __init__(self, in_features: int, out_features: int, bias: bool = True):
            super().__init__()
            self.in_features = in_features
            self.out_features = out_features
            self.weight_self = nn.Linear(in_features, out_features, bias=bias)
            self.weight_neigh = nn.Linear(in_features, out_features, bias=False)
            self.reset_parameters()

        def reset_parameters(self):
            nn.init.kaiming_uniform_(self.weight_self.weight, a=math.sqrt(5))
            nn.init.kaiming_uniform_(self.weight_neigh.weight, a=math.sqrt(5))

        def forward(self, x: torch.Tensor, adj_matrix: torch.Tensor) -> torch.Tensor:
            """
            x: (N, in_features)
            adj_matrix: (N, N) normalized or binary adjacency matrix
            """
            # Degree normalization for mean aggregation
            deg = torch.sum(adj_matrix, dim=1, keepdim=True)
            deg = torch.clamp(deg, min=1.0)
            neigh_agg = torch.matmul(adj_matrix, x) / deg

            out = self.weight_self(x) + self.weight_neigh(neigh_agg)
            return out


    class GraphSAGEClassifier(nn.Module):
        """
        3-Layer GraphSAGE Architecture with Dual Heads:
        Head 1: Entity Category (exchange, mixer, mule, unknown)
        Head 2: VASP Attribution (Binance, FixedFloat, Tornado.Cash, ChangeNOW, Coinbase, Other)
        """

        CATEGORIES = ["exchange", "mixer", "mule", "unknown"]
        VASPS = ["Binance", "FixedFloat", "Tornado.Cash", "ChangeNOW", "Coinbase", "Other"]

        def __init__(self, in_dim: int = 16, hidden_dim: int = 64, embed_dim: int = 32, dropout: float = 0.2):
            super().__init__()
            self.layer1 = GraphSAGELayer(in_dim, hidden_dim)
            self.layer2 = GraphSAGELayer(hidden_dim, hidden_dim)
            self.layer3 = GraphSAGELayer(hidden_dim, embed_dim)

            self.bn1 = nn.BatchNorm1d(hidden_dim)
            self.bn2 = nn.BatchNorm1d(hidden_dim)
            self.dropout = nn.Dropout(dropout)

            # Classification heads
            self.category_head = nn.Linear(embed_dim, len(self.CATEGORIES))
            self.vasp_head = nn.Linear(embed_dim, len(self.VASPS))

        def forward(self, x: torch.Tensor, adj: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """
            Returns:
              category_probs: (N, 4)
              vasp_probs: (N, 6)
              embeddings: (N, embed_dim)
            """
            h1 = F.relu(self.layer1(x, adj))
            if x.size(0) > 1:
                h1 = self.bn1(h1)
            h1 = self.dropout(h1)

            h2 = F.relu(self.layer2(h1, adj))
            if x.size(0) > 1:
                h2 = self.bn2(h2)
            h2 = self.dropout(h2)

            embeds = F.relu(self.layer3(h2, adj))

            cat_logits = self.category_head(embeds)
            vasp_logits = self.vasp_head(embeds)

            cat_probs = F.softmax(cat_logits, dim=-1)
            vasp_probs = F.softmax(vasp_logits, dim=-1)

            return cat_probs, vasp_probs, embeds

else:
    class GraphSAGEClassifier:  # type: ignore
        CATEGORIES = ["exchange", "mixer", "mule", "unknown"]
        VASPS = ["Binance", "FixedFloat", "Tornado.Cash", "ChangeNOW", "Coinbase", "Other"]
