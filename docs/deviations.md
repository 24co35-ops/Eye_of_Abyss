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
