# Eye of Abyss — Design Document

**Version:** 0.1  
**Status:** Draft  

---

## 1. System Architecture

### 1.1 Design Principles

**Microservices-first.** Each module (VoiceGuard, ShadowTrace, ChainEye) is an independently deployable service. The Case Engine orchestrates across them but does not depend on all three being operational — a case can proceed with one or two module submissions. This allows the demo to work even if one module is still being built.

**Evidence-object model.** Every module produces a standardized Evidence Object, not a raw prediction. The Evidence Object is the unit of case construction — it contains the verdict, artifacts, confidence, and enough context to be court-admissible without the original inference system being present.

**Graph as shared substrate.** The criminal actor graph is not a module-specific data structure — it is shared infrastructure that both ShadowTrace (identity graph) and ChainEye (transaction graph) populate, and the Case Engine reads for cross-module convergence.

**Blockchain is audit, not storage.** The chain stores hashes, not data. Evidence files live in Supabase Storage + IPFS. The blockchain is the tamper-evident timestamp, not the database.

---

### 1.2 Service Interaction Map

```
[Investigator] 
    │
    ▼
[Next.js Frontend]
    │
    ├──── Case Create ──────────────────────► [Case Engine :8000]
    │                                               │
    │                                     ┌─────────┼──────────────┐
    │                                     ▼         ▼              ▼
    ├──── Audio Upload ──────────► [VoiceGuard    [ShadowTrace  [ChainEye
    │     (WebSocket/REST)              :8001]       :8002]        :8003]
    │                                     │            │              │
    ├──── Text Sample ────────────────────┘            │              │
    │                                                  │              │
    └──── Wallet Address ──────────────────────────────┘              │
                                                                      │
    [All modules] ──── Evidence Object ──────────────► [Case Engine]
                                                            │
                                           ┌────────────────┤
                                           │                │
                                           ▼                ▼
                                    [PostgreSQL]      [Neo4j Graph]
                                    [Supabase]
                                           │
                                           ▼
                                    [Polygon]
                                    [IPFS/Pinata]
```

---

### 1.3 Evidence Object Schema

Standard contract between all module services and the Case Engine.

```python
class EvidenceObject(BaseModel):
    # Identity
    evidence_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    module_id: Literal['voiceguard', 'shadowtrace', 'chaineye']
    created_at: datetime
    created_by: str  # Officer ID

    # Verdict
    verdict: str              # Human-readable: "Synthetic voice detected"
    verdict_code: str         # Machine-readable: "SYNTHETIC_TTS"
    confidence: float         # 0.0 – 1.0
    confidence_tier: Literal['high', 'medium', 'low']

    # Module-specific payload
    payload: dict             # Module-specific structured data

    # Artifacts
    artifacts: list[Artifact] # Files, graphs, visualizations

    # Chain of custody
    submitted_by: str         # Officer ID
    submitted_at: datetime
    hash_sha256: str          # Computed over evidence_id + payload + artifacts
    chain_anchor: Optional[str]  # Polygon tx hash (None until anchored)
    ipfs_cid: Optional[str]

    # Cross-module signals (populated by Case Engine)
    cross_signals: Optional[CrossModuleSignals] = None


class CrossModuleSignals(BaseModel):
    timezone_match: Optional[float]       # Correlation between ShadowTrace and ChainEye timezone
    activity_overlap: Optional[float]     # Operational period overlap score
    actor_graph_link: Optional[str]       # Neo4j node ID linking both
    convergence_confidence: Optional[float]  # Combined confidence
```

---

## 2. Module Internal Designs

### 2.1 VoiceGuard — Inference Pipeline

```
Audio Input (WebSocket chunks / File upload)
    │
    ▼
Preprocessing
├── Resample to 16kHz
├── Normalize amplitude
├── Split into 2s overlapping windows (50% overlap)
└── Apply noise reduction (noisereduce)
    │
    ▼
Feature Extraction
├── MFCC (40 coefficients)
├── Spectral flatness
├── Mel spectrogram
└── Raw waveform (for Wav2Vec2 branch)
    │
    ▼
Dual-branch inference
├── Branch A: DistilWav2Vec2 → sigmoid → synthetic probability
└── Branch B: ECAPA-TDNN → softmax → [real, TTS, voice_conv, replay]
    │
    ▼
Score fusion
├── Weighted average (Branch A: 0.6, Branch B: 0.4)
├── Threshold: synthetic if P(synthetic) > 0.72
└── Uncertainty band: 0.45 – 0.72 → "uncertain"
    │
    ▼
Evidence Object construction
├── Verdict + confidence
├── Flagged segment timestamps
├── MFCC heatmap artifact
└── Spectrogram artifact
```

**Latency budget (GPU):**
```
Preprocessing:     ~15ms
Feature extraction: ~10ms
Inference:         ~150ms  ← dominant cost
Fusion + output:    ~5ms
Total:             ~180ms  ← within 200ms target
```

---

### 2.2 ShadowTrace — Stylometry Pipeline

```
Text Input (raw string)
    │
    ▼
Preprocessing
├── Language detection (langdetect)
├── Tokenization (SpaCy)
├── POS tagging
└── Dependency parsing
    │
    ▼
Feature Extraction
├── Lexical features
│   ├── Type-token ratio
│   ├── Average word length
│   ├── Hapax legomena ratio
│   └── Vocabulary richness (Yule's K)
├── Syntactic features
│   ├── Average sentence length
│   ├── Sentence length variance
│   ├── Subordinate clause ratio
│   └── Punctuation frequency vector
├── Character n-grams (n=3,4,5)
│   └── TF-IDF weighted, 10,000 most common
└── BERT embedding
    └── [CLS] token from fine-tuned encoder
    │
    ▼
Fingerprint Vector
├── Concatenate all features
├── L2 normalize
└── Store in pgvector (1536-dim)
    │
    ▼
Attribution
├── Query pgvector: k-NN search (k=5) against known actor corpus
├── Compute cosine similarity
└── Return top-k matches with confidence
    │
    ▼
Temporal Analysis (if timestamp available)
├── Extract posting hour UTC
├── Build activity distribution (24-bin histogram)
├── FFT for periodicity detection
└── Infer most likely timezone
```

---

### 2.3 ChainEye — Graph Pipeline

```
Wallet Address Input
    │
    ▼
Transaction Graph Construction
├── Fetch transactions (Etherscan / Blockstream API)
├── Multi-hop expansion (depth=3 by default)
├── Build directed graph (wallet nodes, tx edges)
└── Store in Neo4j
    │
    ▼
Heuristic Clustering
├── Co-spend analysis (multi-input transactions)
├── Change address detection
├── Peeling chain detection
└── Merge into wallet cluster
    │
    ▼
GNN Inference (GraphSAGE)
├── Node features: tx count, volume, age, mixer flags
├── 3-layer GraphSAGE
├── Output: wallet category (exchange, mixer, mule, unknown)
└── VASP attribution via classification head
    │
    ▼
Withdrawal Prediction (XGBoost)
├── Input features:
│   ├── Inflow amount
│   ├── Wallet age
│   ├── Dormancy pattern
│   ├── Complaint lag distribution (from actor profile)
│   └── Historical withdrawal hour distribution
└── Output: predicted withdrawal window + confidence
    │
    ▼
Evidence Object construction
├── Wallet cluster graph (Cytoscape JSON)
├── VASP attribution + confidence
├── Withdrawal prediction alert
└── Transaction flow artifacts
```

---

## 3. Case Engine — State Machine

```
CREATED ──────────────────────────────────────────► (complaint intake complete)
    │
    ▼
ACTIVE ─── [module submissions arrive] ────────────► (1+ evidence objects filed)
    │
    ▼
EVIDENCE_SUBMITTED ──── [all assigned modules submit] ──► or manual override
    │
    ▼
CONVERGENCE_COMPUTED ── [cross-module signals computed] ─► auto, if 2+ modules
    │
    ▼
READY_TO_ANCHOR ───────── [supervisor review complete] ──► manual approval
    │
    ▼
ANCHORED ──────────────── [Polygon tx confirmed] ────────► auto, < 30s
    │
    ▼
FILED ────────────────── [PDF exported, freeze drafted] ─► manual action
    │
    ▼
CLOSED ───────────────── [case resolution recorded] ─────► manual action
```

**Cross-module convergence trigger:**
When 2 or more modules submit evidence for the same case, the Case Engine automatically:
1. Extracts timezone signal from ShadowTrace temporal profile
2. Extracts preferred withdrawal hours from ChainEye wallet profile
3. Computes overlap score
4. Extracts operational period from both modules
5. Checks Neo4j shared actor graph for existing links
6. Generates convergence report with composite confidence

---

## 4. Blockchain Evidence Anchoring

### Evidence Registry Smart Contract (Solidity)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EvidenceRegistry {
    struct EvidenceRecord {
        bytes32 evidenceHash;    // SHA-256 of evidence object
        uint256 timestamp;
        address submittedBy;
        string caseId;           // UUID string
        string moduleId;
        string ipfsCid;
    }

    mapping(bytes32 => EvidenceRecord) public records;
    mapping(string => bytes32[]) public caseEvidence; // caseId → evidence hashes

    event EvidenceAnchored(
        bytes32 indexed evidenceHash,
        string caseId,
        string moduleId,
        uint256 timestamp
    );

    function anchor(
        bytes32 evidenceHash,
        string memory caseId,
        string memory moduleId,
        string memory ipfsCid
    ) external {
        require(records[evidenceHash].timestamp == 0, "Already anchored");

        records[evidenceHash] = EvidenceRecord({
            evidenceHash: evidenceHash,
            timestamp: block.timestamp,
            submittedBy: msg.sender,
            caseId: caseId,
            moduleId: moduleId,
            ipfsCid: ipfsCid
        });

        caseEvidence[caseId].push(evidenceHash);

        emit EvidenceAnchored(evidenceHash, caseId, moduleId, block.timestamp);
    }

    function verify(bytes32 evidenceHash) external view returns (bool, uint256) {
        EvidenceRecord memory r = records[evidenceHash];
        return (r.timestamp > 0, r.timestamp);
    }
}
```

### Anchoring Flow (Python — Case Engine)

```python
async def anchor_evidence(evidence: EvidenceObject) -> str:
    # 1. Pin to IPFS
    ipfs_result = await pinata.pin_json(evidence.dict())
    cid = ipfs_result['IpfsHash']

    # 2. Compute evidence hash
    evidence_bytes = json.dumps(evidence.dict(), sort_keys=True).encode()
    evidence_hash = hashlib.sha256(evidence_bytes).digest()
    evidence_hash_hex = '0x' + evidence_hash.hex()

    # 3. Submit to Polygon
    tx = await evidence_registry.functions.anchor(
        evidence_hash_hex,
        str(evidence.case_id),
        evidence.module_id,
        cid
    ).transact({'from': deployer_address})

    receipt = await web3.eth.wait_for_transaction_receipt(tx)
    tx_hash = receipt['transactionHash'].hex()

    # 4. Update evidence record
    await db.update_evidence_anchor(evidence.evidence_id, tx_hash, cid)

    return tx_hash
```

---

## 5. Data Pipeline — Design Decisions

### 5.1 Why a Shared Schema

The criminal actor behaves consistently across domains. The same person who posts on a forum at 2am UTC also withdraws cryptocurrency at 2am UTC. The same person who uses particular linguistic patterns also operates wallets with predictable dormancy cycles. The shared Criminal Actor Profile schema captures this correlation as a design fact, not an afterthought.

The consequence: cross-module correlation features in the Case Engine convergence report are not heuristics — they are trained expectations from the same underlying data generation process.

### 5.2 Synthetic Data Transparency

All synthetic data carries `"data_source": "synthetic"` in its metadata. Training metrics are reported separately for:
- Synthetic-only training set
- Gwern corpus fine-tuning (where applicable)
- Mixed training (synthetic + public academic datasets)

This transparency is a feature, not a limitation — it demonstrates the pipeline's calibration methodology and acknowledges what production deployment requires (agency partnership for real corpus data).

### 5.3 Gwern Archive Integration

The Gwern DNM archives bridge both modules:
- Forum posts → ShadowTrace stylometry corpus (vendor communications, forum posts)
- Transaction logs → ChainEye behavioral calibration (withdrawal patterns, dormancy cycles)
- Vendor-transaction links → Cross-module ground truth (same actor appearing in both domains)

Processing pipeline:
```
gwern_raw/
├── silkroad2/     → parse vendor handles, forum posts, timestamps
├── agora/         → same
└── alphabay/      → same
    │
    ▼
extract_actors.py  → actor handle → post list + tx list
    │
    ├──► corpus/actor_{id}/posts.txt  → ShadowTrace input
    └──► txs/actor_{id}_txs.csv       → ChainEye calibration input
```

---

## 6. API Contracts

### Case Engine — Module-facing API

```
POST /cases
POST /cases/{case_id}/evidence          ← Module evidence submission
GET  /cases/{case_id}
GET  /cases/{case_id}/convergence       ← Cross-module convergence report
POST /cases/{case_id}/anchor            ← Trigger blockchain anchoring
GET  /cases/{case_id}/export            ← PDF case file export
```

### VoiceGuard API

```
POST /analyze/file          ← Upload audio file
WS   /analyze/stream        ← Real-time WebSocket stream
GET  /analysis/{job_id}     ← Poll result
GET  /analysis/{job_id}/artifacts   ← Download artifacts
```

### ShadowTrace API

```
POST /fingerprint           ← Submit text sample, get fingerprint vector
POST /attribute             ← Attribute text to known actor corpus
GET  /actors/{actor_id}     ← Get known actor profile
POST /actors                ← Add actor sample to corpus
GET  /graph/export          ← Export actor network graph
```

### ChainEye API

```
POST /trace/wallet          ← Submit wallet address
POST /trace/transaction     ← Submit tx hash
GET  /trace/{job_id}        ← Poll trace result
GET  /attribution/{address} ← VASP attribution lookup
POST /predict/withdrawal    ← Withdrawal window prediction
GET  /graph/{wallet_id}     ← Export wallet cluster graph
```

---

## 7. Security Design

### Authentication
- JWT-based, issued by Case Engine
- Access token: 15-minute expiry
- Refresh token: 7-day expiry, stored httpOnly
- Officer wallet (MetaMask) for blockchain operations — separate from platform auth

### Authorization
```
Role: INVESTIGATOR
  ├── Create cases, submit evidence
  ├── View own cases + shared cases
  └── Cannot anchor (requires supervisor)

Role: SUPERVISOR
  ├── All INVESTIGATOR permissions
  ├── Approve evidence for anchoring
  └── View all cases in unit

Role: ADMIN
  ├── All SUPERVISOR permissions
  ├── Manage officers, units
  └── System configuration
```

### Data Classification
```
RESTRICTED:    Victim PII, complaint data → encrypted at rest, access logged
CONFIDENTIAL:  Case files, evidence objects → encrypted at rest
INTERNAL:      Module inference results → standard security
PUBLIC:        Blockchain anchors → public by design (hash only)
```

---

## 8. Visual Identity & UI Design System

### Design Philosophy
The interface must embody the Nietzschean tension: institutional authority (an investigation tool) and the darkness it navigates (the criminal underworld). Not hacker-aesthetic. Not government-grey. Something that communicates both the weight of consequence and the precision of intelligence work.

**Typefaces:**
- `Space Grotesk` — display, headings. Humanist geometric sans-serif with a slightly technical edge. Conveys precision without coldness.
- `JetBrains Mono` — data, hashes, wallet addresses, code. Monospace for everything that is a string of consequence.

**Color System:**

| Token | Hex | Role |
|---|---|---|
| `--abyss` | `#0D0B14` | Primary background — deep, violet-tinted black |
| `--void` | `#13111E` | Surface — slightly lifted from background |
| `--shadow` | `#1C1929` | Card surface, input fields |
| `--mist` | `#2A2640` | Borders, dividers |
| `--gaze` | `#F0A500` | Primary accent — amber gold. The eye in the dark. |
| `--gaze-dim` | `#7A5300` | Muted accent, hover states |
| `--signal` | `#6B4FFF` | Graph edges, attribution confidence |
| `--signal-dim` | `#3D2E99` | Muted signal |
| `--threat` | `#C92A2A` | Alerts, high-confidence synthetic verdict |
| `--safe` | `#2A9D4E` | Confirmed real, low threat |
| `--text-primary` | `#E8E6F2` | Primary text |
| `--text-secondary` | `#8884A8` | Secondary labels, metadata |
| `--text-muted` | `#4A4768` | Disabled, placeholder |

**Why amber gold (`--gaze`) instead of the typical cyber cyan/green:**
Gold connotes intelligence, judgment, authority — the eye that sees, not the terminal that blinks. It reads as deliberate against the deep violet-black background in a way that cyan does not. It avoids the entire visual vocabulary of "hacker tool."

**Layout:**
- Persistent left navigation rail: 56px icon-only (collapsed) / 220px expanded
- Content area: left-aligned, max-width 1400px
- Right context panel: 320px (case context, module status) — slides in on case selection
- Data density: high — investigators need information, not whitespace
- Border radius: 4px consistently (sharp enough to feel precise, not rounded-card generic)

**Motion:**
One orchestrated moment on page load — the case list fades in with a single sweep. Nothing else animates automatically. Module status indicators pulse only when actively processing.

---

## 9. Open Questions & Known Limitations

| Item | Status | Notes |
|---|---|---|
| ShadowTrace: live Tor crawling | Out of scope v0.1 | Static corpus only |
| XMR tracing | Known limitation | Monero's ring signatures defeat current chain analysis; noted as research area |
| NCRP real complaint data | Pending | Requires MHA data-sharing agreement; synthetic data used for v0.1 |
| DarkBERT model access | In progress | Email sent to S2W; multilingual BERT fallback ready |
| VoiceGuard phone-line audio quality | Untested | GSM codec compression affects spectrogram quality; needs evaluation |
| Multi-language stylometry (ShadowTrace) | Partial | English primary; Hindi/regional language support in roadmap |
| Neo4j scaling beyond 1M nodes | Not tested | AuraDB free tier limit: 200k nodes; production requires paid instance |
