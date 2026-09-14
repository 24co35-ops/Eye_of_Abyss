# Product Requirements Document
# Eye of Abyss — Cybercrime Intelligence Suite

**Version:** 0.1  
**Status:** Draft  
**Team:** Crimson Syndicate — Ashwith (24CO35), Shivam  
**Target Submission:** Smart India Hackathon 2026  
**Philosophy:** Friedrich Nietzsche, *Beyond Good and Evil* §146

---

## 1. Problem Statement

India's cybercrime investigation apparatus faces a three-front failure:

**Voice fraud is undetectable in real-time.** AI-generated synthetic voices are used in vishing, impersonation attacks, and KYC bypass. Banks and telecom providers have no infrastructure to flag deepfake audio during an active call. By the time a complaint is filed, the window to act is closed.

**Dark web actors operate with identity impunity.** Criminals fragment their presence across Tor forums, Telegram channels, and clearnet platforms, exploiting the assumption that no single surface reveals enough. No tool currently cross-correlates behavioral signals — writing style, posting cadence, linguistic fingerprints — across platforms to converge on a single actor identity.

**Cryptocurrency trails go cold.** Transaction obfuscation — mixers, chain-hopping, mule accounts, fragmented withdrawals — outpaces manual investigation capacity. Investigators cannot predict withdrawal windows; freeze requests arrive after funds have moved. ChainEye solves the timing problem, not just the attribution problem.

Traditional tools address each of these in isolation. Eye of Abyss treats them as three views of the same actor — and the case only closes when all three converge.

---

## 2. Target Users

### Primary
- **Cybercrime Cell Investigators** (state police, NCRB-affiliated units) — conducting active case investigations across voice fraud, dark web crime, and crypto fraud
- **Financial Intelligence Unit (FIU-IND) Analysts** — tracking suspicious transaction patterns, preparing STR/CTR reports
- **Enforcement Directorate (ED) Officers** — building prosecutable evidence packages for PMLA cases

### Secondary
- **CERT-In Analysts** — threat intelligence gathering, actor attribution
- **CBI Cyber Wing** — high-value case investigation

### Out of Scope
- Public-facing access
- Bank or payment gateway integration (v0.1)
- Real-time ISP-level interception (requires CITA authorization framework, beyond scope)

---

## 3. Platform Philosophy

**"He who fights with monsters should look to it that he himself does not become a monster. And if you gaze long into an abyss, the abyss also gazes back into you."**

The platform embodies both halves of this aphorism:

The first half — *don't become the monster* — governs the ethical architecture: tamper-proof evidence chains, complete audit trails, role-based access, DPDP compliance. In staring into criminal darkness, law enforcement must not cross into it.

The second half — *the abyss gazes back* — governs the operational posture: proactive, predictive, multi-perspective. Eye of Abyss does not wait for criminals to surface. It gazes first.

---

## 4. Module Specifications

### 4.1 VoiceGuard — Real-Time Deepfake Detection

**Purpose:** Detect AI-generated synthetic speech during live calls or from audio evidence files.

**Core capability:** Binary classification (real / synthetic) on audio segments, with a confidence score and artifact type classification (TTS, voice conversion, replay).

**Inputs:**
- Live audio stream via WebSocket (chunked, 2-second windows)
- Audio file upload (WAV, MP3, FLAC, M4A — max 50MB)

**Outputs:**
- Real-time verdict: `real | synthetic | uncertain`
- Confidence score: `0.0 – 1.0`
- Artifact classification: `TTS | voice_conversion | replay | clean`
- Flagged segment timestamps
- Evidence package (audio file + analysis report, ready for case attachment)

**Technical approach:**
- Primary model: DistilWav2Vec2 fine-tuned on ASVspoof 2019/2021 + WaveFake
- Fallback: ECAPA-TDNN (lighter, CPU-viable)
- Feature space: MFCCs, spectral flatness, GAN artifact frequency signatures

**Acceptance criteria:**
- Equal Error Rate (EER) < 5% on ASVspoof 2021 LA eval set
- Inference latency < 200ms per 2s chunk on GPU
- Inference latency < 800ms per 2s chunk on CPU (degraded mode)
- False positive rate < 3% on natural speech samples

---

### 4.2 ShadowTrace — Dark Web De-Anonymization

**Purpose:** Attribute forum handles, Telegram accounts, and dark web vendor profiles to unified actor identities using linguistic fingerprinting, temporal analysis, and network graph correlation.

**Core capability:** Cross-platform actor attribution — given a sample of text from an unknown source, identify which known actor cluster it likely belongs to, with a confidence score.

**Inputs:**
- Raw text sample (forum post, message, vendor description)
- Platform metadata (optional: source platform, timestamp)
- Actor corpus (known samples to compare against)

**Outputs:**
- Actor attribution: matched handle cluster + confidence
- Linguistic fingerprint vector (stored in pgvector)
- Temporal activity profile (posting hours → timezone inference)
- Cross-platform link graph (NetworkX GraphML)
- Evidence report (fingerprint analysis, ready for case attachment)

**Technical approach:**
- Stylometry: fine-tuned BERT encoder on PAN@CLEF authorship data, adapted on Gwern DNM corpus
- Features: character n-grams, POS tag distributions, syntactic complexity, punctuation profiles, vocabulary richness
- Temporal analysis: Fourier analysis on posting timestamp distributions, timezone inference
- Network graph: co-posting edges, referral mentions, transaction co-occurrence

**Acceptance criteria:**
- Top-1 author attribution accuracy > 80% on PAN authorship verification task
- Cross-platform consistency score correlation > 0.7 between known same-actor handle pairs
- Temporal analysis produces timezone estimate within ±2 hours for 75% of test profiles

---

### 4.3 ChainEye — Cryptocurrency Forensics

**Purpose:** Trace cryptocurrency flows, attribute wallets to real-world entities (VASPs, known actors), and predict withdrawal timing windows to enable proactive freeze requests.

**Core capability:** Wallet cluster attribution + predictive withdrawal alert, integrated with the NCRP complaint timeline.

**Inputs:**
- Wallet address (BTC, ETH, USDT/ERC-20, MATIC, TRX)
- Transaction hash (optional — start from specific transaction)
- Complaint record (amount, reported timestamp — for withdrawal prediction)

**Outputs:**
- Wallet cluster graph (attribution + co-spend heuristics)
- VASP attribution: exchange identity + confidence
- Withdrawal prediction: estimated window (hours), confidence, recommended freeze deadline
- Transaction flow visualization (Cytoscape.js graph)
- Evidence report (chain of custody, ready for case attachment)

**Technical approach:**
- GNN: GraphSAGE on transaction graph, trained on Elliptic Bitcoin dataset
- Co-spend clustering: heuristic-based (multi-input tx analysis, change address detection)
- VASP attribution: labeled address database + GNN classification
- Withdrawal prediction: XGBoost trained on Gwern/synthetic complaint dynamics data
  - Features: inflow amount, dormancy pattern, wallet age, complaint lag distribution

**Acceptance criteria:**
- Wallet classification F1 > 0.85 on Elliptic dataset test set
- VASP attribution accuracy > 75% on labeled address holdout set
- Withdrawal prediction recall > 70% within ±24h window
- Graph rendering for 500-node wallet cluster < 3 seconds

---

### 4.4 Investigation Case Engine

**Purpose:** Unify evidence from all three modules into a single court-admissible case file, with tamper-proof blockchain anchoring.

**Core capability:** Cross-module evidence convergence — linking a ShadowTrace actor cluster to a ChainEye wallet cluster via shared signals (timezone alignment, operational period overlap, activity pattern correlation).

**Case lifecycle:**
```
CREATED → ACTIVE → EVIDENCE_SUBMITTED → ANCHORED → FILED → CLOSED
```

**Inputs:**
- Complaint intake form
- Module evidence packages (automatically routed on case creation)
- Investigator annotations

**Outputs:**
- Unified case file (PDF export, structured JSON)
- Cross-module convergence report (shared signals between modules)
- Blockchain anchor (Polygon tx hash per evidence milestone)
- IPFS-pinned evidence bundle
- Freeze request draft (pre-filled for submission to bank/exchange)

**Evidence anchoring logic:**
1. Evidence object created in module service
2. SHA-256 hash computed over evidence JSON
3. Hash submitted to Evidence Registry smart contract on Polygon
4. Tx hash stored in case record
5. IPFS pin created for evidence file

**Acceptance criteria:**
- Evidence anchor on Polygon < 30 seconds
- Case file export (PDF) generation < 10 seconds
- Cross-module convergence report generated automatically on ≥2 module submissions
- Complete audit trail for every state transition

---

## 5. Non-Functional Requirements

### Security
- Role-based access control (Investigator, Supervisor, Admin)
- All evidence files encrypted at rest (AES-256, Supabase managed)
- API authentication via JWT with short expiry (15 min access, 7 day refresh)
- No PII stored in blockchain anchor (hashes only)
- Complete audit log of all user actions

### Compliance
- DPDP Act 2023 (India): data minimization, purpose limitation, retention policy
- Victim data (complaint records): retained maximum 5 years, access logged
- Dark web corpus: used for model training only, not stored in production DB
- Financial data: transaction hashes only — no account holder PII unless from agency partner

### Performance
- See Technical Stack performance targets
- Dashboard available offline (core case viewing) — service worker cache
- All module services independently scalable (Docker Compose → Kubernetes path)

### Availability (v0.1 — development/demo)
- Single-node Docker Compose deployment
- No HA requirement for SIH demo
- Recovery from restart < 2 minutes

---

## 6. Out of Scope — v0.1

- Real-time ISP-level call interception
- Direct NCRP API integration (pending MHA partnership)
- Multi-agency tenant isolation (single-agency deployment only)
- Mobile app
- Automatic court filing integration
- ShadowTrace live Tor crawling (corpus is static for v0.1)
- XMR (Monero) tracing (cryptographic limitation — noted as research area)

---

## 7. Success Metrics — SIH Demo

| Metric | Target |
|---|---|
| VoiceGuard live demo: correctly identifies synthetic voice sample | Yes |
| ChainEye: traces provided wallet address to VASP | Yes |
| ChainEye: generates withdrawal prediction with confidence score | Yes |
| ShadowTrace: attributes text sample to correct author in 10-actor corpus | Yes |
| Case Engine: generates unified case file from 2+ module submissions | Yes |
| Evidence anchor: Polygon tx hash visible for demo case | Yes |
| End-to-end demo (complaint → case file → anchor) | < 10 minutes |

---

## 8. Milestones

| Phase | Scope | Duration |
|---|---|---|
| Phase 0 | Data acquisition, API keys, infrastructure setup | Week 1 |
| Phase 1 | ChainEye v0.1 — GNN + wallet attribution API + basic dashboard | Week 2–3 |
| Phase 2 | VoiceGuard v0.1 — inference API + file upload UI | Week 4 |
| Phase 3 | ShadowTrace v0.1 — stylometry pipeline + corpus from Gwern | Week 5–6 |
| Phase 4 | Case Engine — evidence convergence + Polygon anchoring | Week 7 |
| Phase 5 | Full dashboard integration + demo preparation | Week 8 |
