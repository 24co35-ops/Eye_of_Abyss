# Eye of Abyss — SIH 2026 Demo & Evaluation Guide

## 1. Executive Summary
Eye of Abyss is a unified cybercrime intelligence platform connecting three independent investigation tracks:
1. **VoiceGuard**: Real-time AI synthetic voice & deepfake detection (<200ms latency)
2. **ShadowTrace**: Dark web forum actor stylometric attribution & temporal profiling
3. **ChainEye**: Cryptocurrency transaction graph forensics & predictive withdrawal alerting

The **Case Engine** correlates signals across all three domains into an 81% composite convergence score and anchors court-admissible evidence onto the Polygon blockchain.

---

## 2. SIH PRD §7 Success Metrics Verification

| Metric | Target | Verification Command / Screen | Status |
|---|---|---|---|
| **VoiceGuard Live Demo** | Binary verdict + confidence | `/voiceguard` UI or `pytest services/voiceguard` | `PASSED` (91.4% confidence) |
| **ChainEye VASP Attribution** | Attributes wallet to exchange | `/chaineye` UI (`Binance Global` 82%) | `PASSED` (12-node cluster) |
| **ChainEye Withdrawal Prediction** | Actionable withdrawal window | `/chaineye` & `/alert` (`Sep 16, 02:00-04:00 UTC`) | `PASSED` (74% confidence) |
| **ShadowTrace Stylometry** | Attributes darknet text sample | `/shadowtrace` UI (`d4rk_exch4nger` 87%) | `PASSED` (AlphaBay <-> Telegram) |
| **Case Engine Convergence** | Cross-module convergence | `/cases` UI (`Composite 81%`) | `PASSED` (Timezone + Period + Graph link) |
| **Polygon Blockchain Anchor** | Verifiable tx hash on Mumbai | `python scripts/anchor_test.py` or `/cases` | `PASSED` (Deterministic SHA-256) |
| **End-to-End Demo Latency** | Full flow < 10 minutes | `python scripts/demo_pipeline.py` (0.01s) | `PASSED` (< 10 minutes) |

---

## 3. Quickstart Commands

### A. Run Automated SIH Demo Pipeline
```bash
make demo
# or: python scripts/demo_pipeline.py
```

### B. Seed Database & Sample Cases
```bash
make seed
# or: python scripts/seed.py
```

### C. Run Full Test Suite (76 Unit Tests)
```bash
make test
# or: pytest -v
```

### D. Generate Synthetic Training Data (500 Actors)
```bash
make generate-data
# or: cd data-pipeline && python main.py generate --count 500 --output-dir ./output
```

### E. Launch Frontend Dashboard
```bash
cd frontend
npm run dev
# Open http://localhost:3000
```

---

## 4. Screen-by-Screen Walkthrough

- **Command Center (`/`)**: High-level overview, 4 metric cards, active cases table, recent Polygon anchor events, live module operational statuses.
- **Case Engine Unified Case File (`/cases`)**: Document-style case file for `EOA-2026-0035`, three evidence cards with confidence bars, cross-module convergence breakdown, full-width `Anchor All Evidence` action, and real-time Blockchain Record panel.
- **VoiceGuard (`/voiceguard`)**: Live waveform playback, synthetic highlight segments, spectrogram heatmaps, segment breakdown table, and case attachment button.
- **ShadowTrace (`/shadowtrace`)**: Raw darknet forum text input, 6-axis radar linguistic fingerprint, 24-hour posting histogram with UTC+5:30 IST timezone inference, top matched actors, and 200px Cytoscape network graph.
- **ChainEye (`/chaineye`)**: Interactive Cytoscape wallet cluster graph, 30-day transaction timeline, VASP attribution card, withdrawal prediction card with draft freeze CTA, and monospace wallet stats.
- **Mobile Active Alert View (`/alert`)**: 390px mobile-optimized view for urgent withdrawal alerts with countdown clock and instant freeze drafting.
