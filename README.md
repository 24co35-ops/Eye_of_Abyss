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
    │  (PyTorch · :8001)  │  │  (BERT+Graph · :8002)  │  │  (Web3/GNN · :8003) │
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

**Port map:**

| Service | Port |
|---|---|
| Case Engine | 8000 |
| VoiceGuard | 8001 |
| ShadowTrace | 8002 |
| ChainEye | 8003 |
| Frontend | 3000 |
| Nginx (reverse proxy) | 80 |

---

## Security Hardening & Architecture

Eye of Abyss is hardened according to enterprise cyberdefense standards:

### 1. Secrets & Runtime Validation
- **Fail-Fast Startup**: Services immediately reject missing, default (`changeme`), or weak credentials with strict minimum length (16-32 chars) and character entropy checks.
- **Zero Default Secrets**: Development fallbacks are high-entropy deterministic hashes; production mode requires all secrets to be explicitly provided in `.env`.

### 2. Authentication & Authorization Scoping
- **Role Hierarchy**: Strict permission gates (`OWNER` > `SUPERVISOR` > `INVESTIGATOR` > `VIEWER`). Only `OWNER` can provision `OWNER` or `SUPERVISOR` accounts.
- **Registration Controls**: Public `/auth/register` requires a cryptographically random `INVITE_TOKEN` in production or is disabled entirely. Public wallet auto-registration is disabled in production.
- **Refresh Token Rotation & Revocation**: Refresh tokens carry unique JTIs and are tracked in Redis/DB with automatic revocation upon rotation or logout.
- **Cookie Security**: Auth cookies are enforced with `HttpOnly`, `SameSite=Strict`, and `Secure` flags.
- **Case Access Scoping**: Regular investigators only view cases they created or are assigned to; supervisors and owners retain audit-level visibility.

### 3. Network Isolation & Infrastructure Defense
- **Docker Network Segmentation**: Two distinct networks — `app_tier` (bridge) and `db_tier` (`internal: true`). Databases cannot access the public internet or be accessed directly from outside Docker.
- **No Database Ports Published**: PostgreSQL (5432), Neo4j (7474/7687), Redis (6379), and MinIO (9000/9001) are unexposed to the host machine.
- **Redis AUTH**: Redis is protected by mandatory authentication passwords (`--requirepass`).
- **Nginx Reverse Proxy & TLS**: Single point of ingress on port 80/443 terminating TLSv1.2/1.3, enforcing HTTP-to-HTTPS redirection, and serving strict headers.

### 4. Middleware & Abuse Protection
- **Sliding-Window Rate Limiting**: Distributed Redis-backed rate limiting with sliding-window ZSET counters across replicas.
- **Request Body & Upload Limits**: Hard 50MB payload limits enforced at both Nginx and ASGI middleware (`RequestBodyLimitMiddleware`).
- **SSRF Defense for Webhooks**: Webhook dispatch blocks private/loopback/reserved CIDR blocks, requires HTTPS, and checks an optional domain allowlist (`ALLOWED_WEBHOOK_DOMAINS`).
- **Persistent Webhook Storage**: Webhook subscriptions persist in Redis/Postgres rather than volatile memory.
- **Security Headers**: Injects `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy`.

### 5. Storage & File Security
- **File Validation**: Uploaded files undergo extension blocklist inspection, MIME type verification, and magic-byte signature validation (audio/pdf/images).
- **Malware Scanning Hook**: Optional ClamAV antivirus integration and embedded executable/script detection.
- **S3 Bucket Hardening**: Enforces SSE-S3 bucket encryption and blocks public ACL access.

### 6. Smart Contract Integrity
- **AccessControl / Ownable**: Only authorized relayer or owner addresses can invoke `anchor()` in `EvidenceRegistry.sol`.
- **Emergency Circuit Breaker**: Contract features pause/unpause functionality and emits indexed `EvidenceAnchored(caseId, sha256, cid, submittedBy)` events for on-chain auditability.

---

## Production Readiness Checklist

Before taking Eye of Abyss to production, verify each requirement:

- [ ] **Generate Secrets**: Run `openssl rand -hex 32` for `JWT_SECRET`, `JWT_REFRESH_SECRET`, `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, `REDIS_PASSWORD`, `MINIO_ROOT_PASSWORD`, and `SEED_OWNER_PASSWORD`.
- [ ] **Set Environment Flag**: Confirm `ENVIRONMENT=production` in `.env`.
- [ ] **Configure CORS**: Define explicit trusted domains in `CORS_ORIGINS` (wildcards will trigger startup rejection).
- [ ] **Lock Registration**: Generate an `INVITE_TOKEN` and ensure `ALLOW_WALLET_AUTOREGISTER=false`.
- [ ] **TLS Certificates**: Place valid SSL certificates (`fullchain.pem` and `privkey.pem`) into `infrastructure/certs/`.
- [ ] **Port Audit**: Confirm only port 80 and 443 are publicly accessible. Verify database ports (5432, 7474, 7687, 6379, 9000, 9001) are unreachable from the host.
- [ ] **Webhooks**: Define `ALLOWED_WEBHOOK_DOMAINS` for third-party SIEM/alert integrations.
- [ ] **Smart Contract**: Deploy `EvidenceRegistry.sol` to your EVM network, grant the relayer key permission via `setRelayer()`, and set `EVIDENCE_REGISTRY_ADDRESS`.
- [ ] **Health Probes**: Verify all services return HTTP 200 on `/health/cases`, `/health/voice`, `/health/shadow`, and `/health/chain`.

---

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose v2.x

### 1. Clone & Configure

```bash
git clone https://github.com/24co35-ops/Eye_of_Abyss.git
cd Eye_of_Abyss
cp .env.example .env
# Edit .env — set JWT_SECRET, POSTGRES_PASSWORD, NEO4J_PASSWORD at minimum
```

### 2. Start the Stack

**Recommended (Makefile — works everywhere):**

```bash
make up
# Equivalent to: docker-compose -f infrastructure/docker-compose.yml up --build
```

**Or call the infrastructure file directly:**

```bash
docker-compose -f infrastructure/docker-compose.yml up --build
```

**PowerShell (Windows, local dev without Docker):**

```powershell
./run.ps1
```

**Hardened Production:**

```bash
docker-compose -f infrastructure/docker-compose.prod.yml up -d --build
```

### 3. Access

| Endpoint | URL |
|---|---|
| Command Center (browser) | http://localhost:3000 |
| Nginx reverse proxy | http://localhost:80 |
| Case Engine API | http://localhost:8000/docs |
| VoiceGuard API | http://localhost:8001/docs |
| ShadowTrace API | http://localhost:8002/docs |
| ChainEye API | http://localhost:8003/docs |

### 4. Local Dev (no Docker)

For frontend-only development against running services, create `frontend/.env.local`:

```bash
cp frontend/.env.local.example frontend/.env.local
# Values default to localhost:800x for local backends
```

Then:

```bash
make frontend     # starts Next.js dev server on :3000
make dev-case-engine   # starts case engine on :8000
```

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
