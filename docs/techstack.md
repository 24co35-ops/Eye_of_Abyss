# Eye of Abyss — Technical Stack

> *"And if you gaze long into an abyss, the abyss also gazes back into you."*
> — Friedrich Nietzsche, Beyond Good and Evil §146

---

## Platform Overview

Eye of Abyss is a microservices-based cybercrime intelligence suite with three parallel investigation modules — VoiceGuard, ShadowTrace, ChainEye — converging into a unified Investigation Case Engine. Each module is independently deployable and exposes a standardized REST + WebSocket API. The platform anchors evidence on-chain for court-admissible tamper-proof audit trails.

---

## Frontend

| Layer | Technology | Rationale |
|---|---|---|
| Framework | Next.js 14 (App Router) | SSR for investigator dashboard, RSC for data-heavy case views |
| Language | TypeScript | Type safety across module API contracts |
| Styling | Tailwind CSS + custom design tokens | Utility-first, consistent with Eye of Abyss visual system |
| State | Zustand | Lightweight, no boilerplate — case state, module status |
| Server State | TanStack Query v5 | API caching, background refetch for live case data |
| Graph Visualization | Cytoscape.js | Wallet attribution graphs, criminal network graphs |
| Audio Visualization | WaveSurfer.js | Real-time waveform in VoiceGuard |
| Charts | Recharts | Temporal analysis, transaction timelines |
| Websockets | native WebSocket API | VoiceGuard real-time inference stream |
| Icons | Lucide React | Consistent, minimal |
| Fonts | Space Grotesk (display) + JetBrains Mono (data) | Identity-specific — not Inter defaults |

---

## Backend — Module Services

Each module is an independent FastAPI microservice. Inter-service communication via internal REST. The Case Engine orchestrates across all three.

### VoiceGuard Service
| Component | Technology |
|---|---|
| Runtime | Python 3.11, FastAPI |
| Inference | PyTorch 2.x + Torchaudio |
| Primary model | DistilWav2Vec2 (distilled for latency) |
| Fallback model | ECAPA-TDNN (CPU-viable) |
| Audio streaming | WebSocket endpoint, 2s chunk window |
| Feature extraction | Librosa + Torchaudio |
| Model serving | Custom FastAPI endpoint (no Triton for v0.1) |

### ShadowTrace Service
| Component | Technology |
|---|---|
| Runtime | Python 3.11, FastAPI |
| Base encoder | DarkBERT (if access granted) / multilingual BERT fallback |
| Stylometry pipeline | Scikit-learn + custom feature extractors |
| Temporal analysis | NumPy, Pandas |
| Network graph | NetworkX (v0.1), Neo4j migration (v1.0) |
| Text preprocessing | SpaCy (en_core_web_lg) |
| Fingerprint storage | pgvector extension on PostgreSQL |

### ChainEye Service
| Component | Technology |
|---|---|
| Runtime | Python 3.11, FastAPI |
| GNN framework | PyTorch Geometric (PyG) |
| Graph DB | Neo4j 5.x (AuraDB Free for dev, self-hosted for prod) |
| Bitcoin data | Blockstream API + Elliptic dataset |
| Ethereum/EVM data | Alchemy API (Polygon, ETH) + Etherscan API |
| VASP attribution | Custom labeled DB (PostgreSQL) |
| Prediction model | GNN (wallet classification) + XGBoost (withdrawal timing) |
| Co-spend heuristics | Custom Python implementation |

### Investigation Case Engine
| Component | Technology |
|---|---|
| Runtime | Python 3.11, FastAPI |
| Orchestration | Internal REST calls to module services |
| Case state machine | Custom Python state machine |
| Evidence object store | PostgreSQL (Supabase) |
| Cross-module graph | Neo4j — shared actor graph from data pipeline |
| Evidence anchoring | Polygon Mumbai testnet (dev), Polygon Mainnet (prod) |
| IPFS pinning | Pinata SDK |
| Task queue | Celery + Redis |

---

## Data Layer

| Purpose | Technology |
|---|---|
| Primary relational DB | PostgreSQL 16 via Supabase |
| Vector similarity search | pgvector (ShadowTrace fingerprints) |
| Graph database | Neo4j 5.x |
| Cache + message broker | Redis 7 |
| Object storage | Supabase Storage (evidence files, audio clips) |
| Time-series (tx data) | TimescaleDB extension on PostgreSQL |

---

## AI/ML Infrastructure

| Purpose | Technology |
|---|---|
| Training framework | PyTorch 2.x |
| GNN training | PyTorch Geometric |
| Experiment tracking | MLflow (self-hosted or DagsHub) |
| Data versioning | DVC |
| Training environment | Google Colab Pro / Kaggle (GPU) |
| Hyperparameter tuning | Optuna |
| Model serialization | TorchScript + ONNX export |
| Inference optimization | ONNX Runtime |

---

## Blockchain & Evidence Anchoring

| Component | Technology |
|---|---|
| Chain | Polygon (PoS) |
| Testnet | Polygon Mumbai |
| Smart contract | Solidity 0.8.x — Evidence Registry contract |
| Contract framework | Hardhat |
| Web3 SDK | ethers.js (backend) + wagmi (frontend, officer wallet auth) |
| IPFS | Pinata (pinning service) |
| Evidence hash | SHA-256 of evidence object JSON |

**What gets anchored:**
- Case creation event
- Module output snapshots (wallet attribution, actor fingerprint, voice verdict)
- Evidence file hashes
- Case status transitions (open → active → filed)

---

## Synthetic Data Pipeline

| Component | Technology |
|---|---|
| Runtime | Python 3.11 |
| Profile generation | NumPy (statistical sampling) |
| Text generation | Anthropic Claude API (forum post generation) |
| Transaction generation | NumPy + Pandas |
| Graph export | NetworkX → GraphML |
| Calibration data | IC3 2023, NCRP 2024, RBI FIU circulars |

---

## DevOps & Infrastructure

| Component | Technology |
|---|---|
| Containerization | Docker + Docker Compose |
| Service orchestration | Docker Compose (dev), Kubernetes (prod roadmap) |
| Reverse proxy | Nginx |
| CI/CD | GitHub Actions |
| Secret management | GitHub Secrets + `.env` (local dev) |
| Code quality | Ruff (Python linting), ESLint + Prettier (TS) |
| Testing | Pytest (backend), Vitest + Playwright (frontend) |
| API documentation | FastAPI auto-docs (Swagger/ReDoc) |

---

## External APIs & Data Sources

| Source | Purpose | Access |
|---|---|---|
| Etherscan API | EVM transaction data | Free tier, API key |
| Blockstream API | Bitcoin transaction data | Free, API key |
| Alchemy | Polygon/ETH RPC node | Free tier, API key |
| Anthropic Claude API | Synthetic text generation | API key |
| Pinata | IPFS pinning | Free tier, API key |
| ASVspoof 2019/2021 | VoiceGuard training data | Public download |
| WaveFake dataset | Synthetic speech samples | Public download |
| Elliptic Bitcoin dataset | ChainEye GNN training | Academic license |
| Gwern DNM archives | ShadowTrace + ChainEye | Public download |
| PAN@CLEF datasets | Stylometry training | Public registration |

---

## Repository Structure

```
eye-of-abyss/
├── services/
│   ├── voiceguard/          ← FastAPI service
│   ├── shadowtrace/         ← FastAPI service
│   ├── chaineye/            ← FastAPI service
│   └── case-engine/         ← FastAPI service + Celery
├── frontend/                ← Next.js 14 app
├── contracts/               ← Hardhat + Solidity
├── data-pipeline/           ← Synthetic data generator
├── shared/                  ← Shared schemas, types, utils
├── infrastructure/
│   ├── docker-compose.yml
│   └── nginx/
├── docs/                    ← PRD, design doc, this file
└── scripts/                 ← Setup, seeding, deployment scripts
```

---

## Module API Contract (inter-service)

All modules expose a standard evidence object structure to the Case Engine:

```typescript
interface ModuleEvidence {
  module_id: 'voiceguard' | 'shadowtrace' | 'chaineye';
  case_id: string;           // UUID
  evidence_id: string;       // UUID
  confidence: number;        // 0.0 – 1.0
  verdict: string;           // Human-readable
  artifacts: Artifact[];     // Files, graphs, fingerprints
  timestamp: string;         // ISO-8601
  chain_anchor?: string;     // Polygon tx hash (once anchored)
}
```

---

## Performance Targets

| Metric | Target |
|---|---|
| VoiceGuard inference (GPU) | < 200ms per 2s chunk |
| VoiceGuard inference (CPU fallback) | < 800ms per 2s chunk |
| ChainEye wallet query | < 3s for wallet attribution lookup |
| ShadowTrace fingerprint match | < 5s for corpus comparison |
| Evidence anchoring (Polygon) | < 30s (tx confirmation) |
| Dashboard initial load | < 2s (LCP) |
| Case Engine evidence merge | < 1s |
