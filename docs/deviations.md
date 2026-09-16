# Eye of Abyss — Engineering Design Decisions & Deviations

This document tracks intentional architectural choices and adaptations made across Eye of Abyss for maximum reliability, speed, and demonstration resilience.

---

## 1. Graceful Degradation on Heavy ML Dependencies
- **Stylometry BERT / Transformers**: In local or CPU-only test environments, stylometry uses character n-gram extraction, vocabulary richness ($K$), and heuristic stylometry if GPU PyTorch / sentence-transformers are not present or encounter library version mismatch.
- **Audio Preprocessing**: `noisereduce` is wrapped with pass-through fallbacks if native C/C++ audio build dependencies are missing.
- **Why**: Ensures that all test suites, CI runners, and demo scripts run deterministically in < 10 seconds without gigabytes of external weights downloads during live evaluation.

## 2. Blockchain & IPFS Mocking Layer
- **Polygon Mumbai & Pinata**: The system supports live Polygon RPC and Pinata JWT anchoring, while also providing deterministic offline mock transaction hashing when private keys or network credentials are not configured.
- **Deterministic SHA-256**: All evidence objects are canonically serialized (`sort_keys=True`, ISO 8601 timestamps) so the SHA-256 hash is 100% deterministic regardless of platform.

## 3. Data Pipeline & Synthetic Tagging
- **Explicit Attribution**: Every generated record in `data-pipeline/output/` is tagged with `"data_source": "synthetic"` to comply with PRD §5 transparency guidelines.
- **NetworkX GraphML**: The actor graph export uses NetworkX GraphML format with node types (`actor`, `wallet`, `platform`, `vasp`) and typed relationships (`OPERATES_WALLET`, `TRANSACTED_WITH`, `POSTED_ON`, `DEPOSITED_TO`).

## 4. Frontend Architecture

- **Next.js 14 App Router**: Static generation with standalone output (`output: "standalone"`) for Docker and instant client-side transitions.
- **Interactive Visualizations**: Cytoscape.js for force-directed actor and wallet graphs, custom SVG radar charts, and WaveSurfer.js audio waveforms.

---

## 5. Docker Networking & NEXT_PUBLIC_* URLs

**Problem:** `NEXT_PUBLIC_*` environment variables are baked into the Next.js bundle at build time and are executed by the browser (host machine), not inside the Docker network. Setting them to `http://case-engine:8000` breaks the browser because `case-engine` is not a hostname the host DNS can resolve.

**Decision:** All API traffic is routed through the **nginx reverse proxy on port 80**, which is the only service with a public host port mapping for API calls. The browser calls `http://localhost/api/cases`, `http://localhost/api/voice`, etc., and nginx proxies to the internal Docker service names.

```
Browser (host) → http://localhost/api/cases → nginx:80 → case-engine:8000
Browser (host) → http://localhost/api/voice  → nginx:80 → voiceguard:8001
Browser (host) → http://localhost/api/shadow → nginx:80 → shadowtrace:8002
Browser (host) → http://localhost/api/chain  → nginx:80 → chaineye:8003
```

For local non-Docker development, copy `frontend/.env.local.example` to `frontend/.env.local` — Next.js loads it automatically, pointing `NEXT_PUBLIC_*` to `http://localhost:800x` directly.

---

## 6. Standardized Port Assignments

| Service | Port | Rationale |
|---|---|---|
| Case Engine | 8000 | Primary orchestrator, lowest number |
| VoiceGuard | 8001 | Module 1 (audio) |
| ShadowTrace | 8002 | Module 2 (text/identity) |
| ChainEye | 8003 | Module 3 (blockchain) |
| Frontend | 3000 | Next.js default |
| Nginx | 80 | Standard HTTP; single browser origin |

These ports are consistent across `infrastructure/docker-compose.yml`, `.env.example`, `frontend/.env.local.example`, `Makefile`, and the README architecture diagram. The earlier deviation where ShadowTrace showed `:8003` and ChainEye showed `:8002` in the README diagram has been corrected.

---

## 7. Neo4j Readiness

Neo4j 5.x takes 20–40 seconds to fully start the Bolt server after the container is running. Services that depend on Neo4j (`shadowtrace`, `chaineye`) now use `condition: service_healthy` against a Neo4j healthcheck that polls the HTTP browser port (7474). This replaces the previous bare `depends_on` list that caused connection errors on first boot.

