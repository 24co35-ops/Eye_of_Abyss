# Eye of Abyss

> *"He who fights with monsters should look to it that he himself does not become a monster.*
> *And if you gaze long into an abyss, the abyss also gazes back into you."*
>
> — Friedrich Nietzsche, *Beyond Good and Evil* §146

**Eye of Abyss** is a self-hosted, open-architecture cybercrime intelligence & forensics workstation. It converges three parallel investigation tracks — AI voice deepfake detection, dark web stylometric actor attribution, and cryptocurrency transaction forensics — into a single tamper-proof case file anchored on-chain with verifiable cryptographic proofs.

---

## Capabilities

| Module | Purpose & Core Capabilities |
|---|---|
| **VoiceGuard** | Real-time & offline AI deepfake voice detection using a DistilWav2Vec2 + ECAPA-TDNN ensemble. Segment-level analysis, spectrogram generation, and confidence tracking. |
| **ShadowTrace** | Dark web forum and marketplace actor attribution via stylometric fingerprinting (BERT + lexical analysis), temporal pattern correlation, and criminal actor graph exploration. |
| **ChainEye** | Cryptocurrency forensics across Bitcoin & EVM chains. Heuristic wallet clustering, VASP exchange attribution, peeling chain detection, and GNN-based withdrawal timing predictions. |
| **Case Engine** | Cross-module evidence orchestrator. Computes multi-signal convergence, enforces supervisory sign-off, anchors SHA-256 evidence packages to EVM blockchains, pins to IPFS, and exports court-ready PDF case dossiers and exchange freeze requests. |

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │        Investigation Case Engine        │
                    │   Evidence Convergence + Blockchain Anchor│
                    │         (FastAPI · Port 8000)           │
                    └───────────┬─────────┬──────────┬────────┘
                                │         │          │
               ┌────────────────┘         │          └────────────────┐
               │                          │                           │
    ┌──────────▼──────────┐  ┌────────────▼────────────┐  ┌──────────▼──────────┐
    │     VoiceGuard      │  │      ShadowTrace        │  │      ChainEye       │
    │  Deepfake Detection │  │  Dark Web Attribution   │  │  Crypto Forensics   │
    │ (PyTorch · Port 8001│  │(BERT + Graph · Port 8003│  │ (Web3/GNN · Port 8002│
    └─────────────────────┘  └─────────────────────────┘  └─────────────────────┘
               │                          │                           │
    ┌──────────▼──────────────────────────▼───────────────────────────▼──────────┐
    │                    PostgreSQL + Neo4j + Redis + MinIO                      │
    │                       Evidence Ledger & Actor Graph                        │
    └────────────────────────────────────────────────────────────────────────────┘
                                          │
                               ┌──────────▼────────────┐
                               │  Blockchain Anchoring │
                               │  Polygon / EVM / IPFS │
                               └───────────────────────┘
```

---

## System Hardening & Operational Features

- **Structured Logging**: JSON-formatted output in production (`shared.logging_config`), colored timestamps in development.
- **Security Middleware**: Automatic injection of `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and HSTS headers.
- **Rate Limiting**: Sliding-window rate limiter per IP / JWT token across all public API endpoints.
- **Probes**: `/health` (liveness) and `/ready` (deep dependency checks) on every microservice.
- **Graceful Lifecycle**: FastAPI async lifespans for clean shutdown and resource cleanup.
- **Strict Environment Configuration**: Zero hardcoded secrets; full runtime configuration via `.env`.

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional for containerized setup)

### 1. Clone & Configure
```bash
git clone https://github.com/24co35-ops/Eye_of_Abyss.git
cd Eye_of_Abyss
cp .env.example .env
```

### 2. Run Locally
**PowerShell (Windows):**
```powershell
./run.ps1
```

**Docker Compose (Development):**
```bash
docker-compose up --build
```

**Docker Compose (Hardened Production):**
```bash
docker-compose -f infrastructure/docker-compose.prod.yml up -d --build
```

Access the Command Center at `http://localhost:3000`.

---

## Extension Points & Developer Guide

### 1. Plugin-Style Module Registration
New forensic modules (e.g. `ImageGuard`, `TelegramScraper`) can be registered with Case Engine dynamically without modifying core orchestrator code:
```bash
curl -X POST http://localhost:8000/modules/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <SUPERVISOR_JWT>" \
  -d '{
    "module_id": "imageguard",
    "name": "ImageGuard AI Forensics",
    "endpoint_url": "http://localhost:8004",
    "icon": "Camera",
    "capabilities": ["deepfake_image_detection", "exif_tampering"]
  }'
```

### 2. Webhook Event Notifications
Subscribe external endpoints to case events (`case.anchored`, `evidence.submitted`, `threat.high_alert`):
```bash
curl -X POST http://localhost:8000/webhooks/subscribe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <SUPERVISOR_JWT>" \
  -d '{
    "url": "https://your-webhook-endpoint.com/eob-events",
    "events": ["case.anchored", "threat.high_alert"]
  }'
```
Payloads are signed with HMAC-SHA256 in the `X-EOB-Signature` header.

### 3. Multi-Chain Anchoring Adapters
Switch networks via the `BLOCKCHAIN_NETWORK` environment variable (`polygon`, `ethereum`, `arbitrum`, or `mock`). Custom adapters can be added in `shared/blockchain_adapters.py`.

### 4. Case Import / Export Bundles
- **Export Case Bundle**: `GET /cases/{case_id}/package` (downloads a `.zip` containing verified metadata, checksums, and artifact files).
- **Import Case Bundle**: `POST /cases/import` (uploads and verifies a case package archive into the database).

---

## Backup & Recovery

Run the automated backup script to create timestamped archives of PostgreSQL/SQLite database files, Neo4j graphs, and evidence artifacts:

```bash
# Python (Cross-platform)
python scripts/backup.py --out-dir ./backups --keep 7

# Bash (Linux/Cron)
chmod +x scripts/backup.sh
./scripts/backup.sh
```

---

## EvidenceObject Contract

All forensic modules submit data adhering to the formal specification detailed in [`docs/EVIDENCE_CONTRACT.md`](./docs/EVIDENCE_CONTRACT.md).

---

## License

MIT License — see [LICENSE](./LICENSE).
