# Eye of Abyss

> *"He who fights with monsters should look to it that he himself does not become a monster.*
> *And if you gaze long into an abyss, the abyss also gazes back into you."*
>
> — Friedrich Nietzsche, *Beyond Good and Evil* §146

**Eye of Abyss** is an open-architecture cybercrime intelligence suite built for law enforcement, financial intelligence units, and cybercrime investigators. It converges three parallel investigation tracks — voice deepfake detection, dark web actor attribution, and cryptocurrency forensics — into a single tamper-proof case file.

The platform does not look away. It gazes first.

---

## What It Does

| Module | What it solves |
|---|---|
| **VoiceGuard** | Detects AI-generated synthetic voices in real-time during calls or from audio evidence files. Flags deepfakes before they can complete a fraud attempt. |
| **ShadowTrace** | Attributes dark web forum handles, Telegram accounts, and marketplace personas to unified criminal identities using linguistic fingerprinting and temporal pattern analysis. |
| **ChainEye** | Traces cryptocurrency flows, maps wallet clusters to real-world exchanges (VASPs), and predicts withdrawal timing windows — enabling proactive freeze requests before funds move. |
| **Case Engine** | Unifies all three modules into a single court-admissible case file. Anchors evidence hashes on the Polygon blockchain. Generates freeze request drafts, convergence reports, and PDF case exports. |

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │         Investigation Case Engine        │
                    │   Evidence Convergence + Blockchain Anchor│
                    └───────────┬─────────┬──────────┬─────────┘
                                │         │          │
               ┌────────────────┘         │          └────────────────┐
               │                          │                           │
    ┌──────────▼──────────┐  ┌────────────▼────────────┐  ┌──────────▼──────────┐
    │     VoiceGuard      │  │      ShadowTrace        │  │      ChainEye       │
    │  Deepfake Detection │  │  Dark Web Attribution   │  │  Crypto Forensics   │
    │  FastAPI + PyTorch  │  │  FastAPI + BERT + NX    │  │  FastAPI + GNN + NJ │
    └─────────────────────┘  └─────────────────────────┘  └─────────────────────┘
               │                          │                           │
    ┌──────────▼──────────────────────────▼───────────────────────────▼──────────┐
    │                    PostgreSQL (Supabase) + Neo4j + Redis                   │
    │                    Shared Criminal Actor Graph (GraphML)                   │
    └────────────────────────────────────────────────────────────────────────────┘
                                          │
                              ┌───────────▼────────────┐
                              │  Polygon Blockchain    │
                              │  Evidence Registry     │
                              │  IPFS (Pinata)         │
                              └────────────────────────┘
```

---

## Philosophical Framework

Eye of Abyss is built on Nietzsche's aphorism — not as aesthetic, but as architecture.

**"Don't become the monster"** → the blockchain evidence anchor, audit trail, DPDP compliance layer, and chain of custody enforcement. In gazing into criminal darkness, the platform ensures law enforcement does not cross into it.

**"The abyss gazes back"** → proactive, not reactive. ChainEye predicts withdrawal windows. ShadowTrace identifies actors before they surface. VoiceGuard flags calls before fraud completes.

**Perspectivism** → no single module reveals truth. The Case Engine is where three partial views — voice, identity, money — converge into a court-admissible picture.

**Will to Power** → not domination, but mastery of domain. ChainEye reclaims the anonymity advantage that currently belongs to criminals.

**Eternal Recurrence** → criminal behavior patterns repeat. Every model is trained on this repetition. The platform treats recurrence as a weapon.

---

## Tech Stack

```
Frontend:    Next.js 14 · TypeScript · Tailwind · Cytoscape.js · WaveSurfer.js
Backend:     FastAPI (per module) · Celery · Redis
AI/ML:       PyTorch · PyTorch Geometric · DistilWav2Vec2 · BERT · XGBoost
Databases:   PostgreSQL/Supabase · Neo4j · pgvector
Blockchain:  Polygon · Solidity · Hardhat · ethers.js · Pinata (IPFS)
Data:        Elliptic · ASVspoof · WaveFake · Gwern DNM · PAN@CLEF
DevOps:      Docker Compose · GitHub Actions · Nginx
```

Full details: [`docs/techstack.md`](./docs/techstack.md)

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Node.js 20+
- Python 3.11+
- Git

### Environment Setup

```bash
git clone https://github.com/24co35-ops/eye-of-abyss.git
cd eye-of-abyss
cp .env.example .env
```

Fill in `.env` — see [Environment Variables](#environment-variables) below.

### Run All Services

```bash
docker-compose up --build
```

Services start at:
- Frontend: `http://localhost:3000`
- VoiceGuard API: `http://localhost:8001`
- ShadowTrace API: `http://localhost:8002`
- ChainEye API: `http://localhost:8003`
- Case Engine API: `http://localhost:8000`
- Neo4j Browser: `http://localhost:7474`

### Run Individual Module (development)

```bash
# ChainEye only
cd services/chaineye
pip install -r requirements.txt
uvicorn main:app --reload --port 8003

# Frontend only
cd frontend
npm install
npm run dev
```

---

## Environment Variables

```env
# Blockchain
POLYGON_RPC_URL=https://polygon-mumbai.g.alchemy.com/v2/YOUR_KEY
PRIVATE_KEY=your_deployer_wallet_private_key
EVIDENCE_REGISTRY_ADDRESS=deployed_contract_address

# Blockchain data APIs
ETHERSCAN_API_KEY=your_key
ALCHEMY_API_KEY=your_key
BLOCKSTREAM_API_KEY=your_key (optional for free tier)

# IPFS
PINATA_API_KEY=your_key
PINATA_SECRET_KEY=your_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/eyeofabyss
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379

# AI API (synthetic data pipeline)
ANTHROPIC_API_KEY=your_key

# Auth
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
```

---

## Data Pipeline — Synthetic Training Data

Eye of Abyss includes a unified synthetic data generator that produces training corpora for both ShadowTrace and ChainEye from a single Criminal Actor Profile schema. This approach allows transparent, reproducible training without access to restricted datasets.

```bash
cd data-pipeline

# Install dependencies
pip install -r requirements.txt

# Generate 500 synthetic actor profiles
python main.py generate \
  --count 500 \
  --archetypes investment_fraudster darknet_vendor ransomware_operator \
  --output-dir ./output

# Outputs:
# ./output/shadowtrace/corpus/         → ShadowTrace training corpus
# ./output/chaineye/transactions.csv   → ChainEye training data
# ./output/chaineye/complaints.csv     → Synthetic NCRP complaint records
# ./output/shared/actor_graph.graphml  → Unified actor graph
```

Full pipeline documentation: [`data-pipeline/README.md`](./data-pipeline/README.md)

---

## Project Structure

```
eye-of-abyss/
├── services/
│   ├── voiceguard/           ← Voice deepfake detection service
│   │   ├── main.py
│   │   ├── models/
│   │   ├── inference/
│   │   └── requirements.txt
│   ├── shadowtrace/          ← Dark web attribution service
│   │   ├── main.py
│   │   ├── stylometry/
│   │   ├── temporal/
│   │   ├── network/
│   │   └── requirements.txt
│   ├── chaineye/             ← Cryptocurrency forensics service
│   │   ├── main.py
│   │   ├── gnn/
│   │   ├── attribution/
│   │   ├── prediction/
│   │   └── requirements.txt
│   └── case-engine/          ← Orchestration + blockchain anchoring
│       ├── main.py
│       ├── state_machine/
│       ├── anchoring/
│       └── requirements.txt
├── frontend/                 ← Next.js 14 dashboard
│   ├── app/
│   ├── components/
│   └── lib/
├── contracts/                ← Solidity evidence registry
│   ├── EvidenceRegistry.sol
│   └── hardhat.config.ts
├── data-pipeline/            ← Synthetic training data generator
│   ├── core/
│   ├── exporters/
│   └── main.py
├── shared/                   ← Shared types, schemas, utils
├── docs/
│   ├── prd.md
│   ├── techstack.md
│   └── design-doc.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Roadmap

- **v0.1** — ChainEye + VoiceGuard core, basic Case Engine, SIH demo scope
- **v0.2** — ShadowTrace full pipeline, cross-module convergence report
- **v0.3** — Multi-agency tenant isolation, Neo4j migration for ShadowTrace
- **v1.0** — Production hardening, Kubernetes deployment, NCRP API integration (pending MHA partnership)
- **Research** — XMR tracing research track (cryptographic limitation acknowledgment)

---

## Team

**Crimson Syndicate** — Agnel Institute of Engineering and Management, Goa

- **Ashwith** (24CO35) — Architecture, ML pipeline, blockchain integration
- **Shivam** — Frontend, API integration, DevOps

**Asura Legion** — Goa-based cybersecurity community (advisory)

---

## Legal & Ethics

- Dark web corpus data used for model training only — not stored in production
- All synthetic data is clearly labeled `data_source: synthetic` in metadata
- DPDP Act 2023 compliance built into Case Engine data layer
- No real victim PII is processed, stored, or transmitted in the development build
- Evidence anchoring stores hashes only — no personal data on-chain

Production deployment requires a formal data-sharing agreement with the relevant law enforcement agency.

---

## License

MIT License — see [LICENSE](./LICENSE)

This project is built for academic and research purposes as part of Smart India Hackathon 2026. Production deployment for law enforcement use requires compliance review by the relevant authority.
# Eye_of_Abyss
