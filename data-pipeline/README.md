# Data Pipeline

Generates synthetic training corpora for ShadowTrace and ChainEye from a unified `CriminalActorProfile` schema.

## Usage

```bash
pip install -r requirements.txt

python main.py generate \
  --count 500 \
  --archetypes investment_fraudster darknet_vendor ransomware_operator \
  --output-dir ./output
```

## Outputs
- `output/shadowtrace/corpus/`       — ShadowTrace training corpus
- `output/chaineye/transactions.csv` — ChainEye training data
- `output/chaineye/complaints.csv`   — Synthetic NCRP complaint records
- `output/shared/actor_graph.graphml`— Unified actor graph
