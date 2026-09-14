# EvidenceObject Contract Specification

The `EvidenceObject` is the fundamental immutable record used across Eye of Abyss. Every intelligence and forensic module (VoiceGuard, ChainEye, ShadowTrace, or custom third-party plugins) submits evidence adhering strictly to this contract.

---

## 1. Schema Definition

```json
{
  "evidence_id": "UUID (v4)",
  "case_id": "UUID (v4)",
  "module_id": "string (e.g. 'voiceguard', 'chaineye', 'shadowtrace', 'custom_plugin')",
  "created_at": "ISO-8601 UTC timestamp",
  "created_by": "string (analyst ID, officer ID, or service)",
  "verdict": "string (human-readable forensic conclusion)",
  "verdict_code": "string (e.g. 'VOICE_SYNTHETIC', 'MIXER_IDENTIFIED', 'STYLOMETRY_MATCH')",
  "confidence": 0.94,
  "confidence_tier": "high | medium | low",
  "payload": {
    "module_specific_key": "module_specific_value"
  },
  "artifacts": [
    {
      "filename": "spectrogram_001.png",
      "file_type": "image/png",
      "description": "Log-mel spectrogram showing synthetic formant patterns",
      "storage_url": "s3://artifacts/cases/001/spectrogram.png"
    }
  ],
  "submitted_by": "string",
  "submitted_at": "ISO-8601 UTC timestamp",
  "hash_sha256": "0x<64-hex-chars>",
  "chain_anchor": "0x<64-hex-chars-tx-hash> (null until anchored)",
  "ipfs_cid": "Qm... (null until pinned)",
  "cross_signals": {
    "timezone_match": 0.85,
    "activity_overlap": 0.92,
    "actor_graph_link": "neo4j_node_id",
    "convergence_confidence": 0.89
  }
}
```

---

## 2. SHA-256 Hash Computation

The integrity of every evidence item is anchored on-chain by its canonical SHA-256 hash.

### Computation Rules:
1. Serialize the dictionary with **alphabetically sorted keys** (`sort_keys=True`).
2. Omit mutable tracking fields (`hash_sha256`, `chain_anchor`, `ipfs_cid`, `cross_signals`).
3. Encode as UTF-8 bytes and compute `hashlib.sha256(raw_bytes).hexdigest()`.

### Python Implementation:
```python
import hashlib
import json

def compute_evidence_hash(payload: dict) -> str:
    keys_to_exclude = {"hash_sha256", "chain_anchor", "ipfs_cid", "cross_signals"}
    clean_dict = {k: v for k, v in payload.items() if k not in keys_to_exclude}
    canonical_json = json.dumps(clean_dict, sort_keys=True, default=str).encode("utf-8")
    return "0x" + hashlib.sha256(canonical_json).hexdigest()
```

### TypeScript Implementation:
```typescript
import { createHash } from "crypto";

export function computeEvidenceHash(payload: Record<string, any>): string {
  const exclude = new Set(["hash_sha256", "chain_anchor", "ipfs_cid", "cross_signals"]);
  const sortedKeys = Object.keys(payload).filter(k => !exclude.has(k)).sort();
  const sortedObj: Record<string, any> = {};
  for (const k of sortedKeys) {
    sortedObj[k] = payload[k];
  }
  const raw = JSON.stringify(sortedObj);
  return "0x" + createHash("sha256").update(raw).digest("hex");
}
```

---

## 3. Developing a Custom Plugin Module

To create a new forensic module that connects to Case Engine:

1. **Expose Health & Readiness**:
   Implement `GET /health` and `GET /ready`.
2. **Register with Case Engine**:
   Post your manifest to `POST http://localhost:8000/modules/register`:
   ```json
   {
     "module_id": "imageguard",
     "name": "ImageGuard AI Forensics",
     "description": "EXIF tampering and diffusion deepfake image detection",
     "version": "1.0.0",
     "endpoint_url": "http://localhost:8004",
     "icon": "Camera",
     "capabilities": ["diffusion_detection", "exif_analysis", "error_level_analysis"],
     "accepted_input_types": ["image/jpeg", "image/png", "image/webp"]
   }
   ```
3. **Submit Evidence**:
   Send POST requests to `POST http://localhost:8000/cases/{case_id}/evidence` with your `ModuleEvidence` payload.
