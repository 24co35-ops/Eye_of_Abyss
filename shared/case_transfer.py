"""Case package export and import utility for Eye of Abyss.

Enables full offline transfer and restoration of cases with all evidence,
convergence reports, blockchain proofs, and raw artifact files.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from datetime import datetime, timezone
from typing import Any

from shared.logging_config import setup_logger

logger = setup_logger("eob.transfer")


def export_case_package(case_dict: dict[str, Any], evidence_list: list[dict[str, Any]], artifacts_map: dict[str, bytes] | None = None) -> bytes:
    """Build a self-contained, verifiable ZIP archive of a case."""
    buf = io.BytesIO()
    
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Main case manifest
        manifest = {
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "case": case_dict,
            "evidence": evidence_list,
            "artifact_count": len(artifacts_map) if artifacts_map else 0,
        }
        manifest_bytes = json.dumps(manifest, indent=2, default=str).encode("utf-8")
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        
        zf.writestr("manifest.json", manifest_bytes)
        zf.writestr("checksum.sha256", f"{manifest_hash}  manifest.json\n")
        
        # 2. Attach artifact binary blobs
        if artifacts_map:
            for filename, data in artifacts_map.items():
                clean_name = os.path.basename(filename)
                zf.writestr(f"artifacts/{clean_name}", data)
                art_hash = hashlib.sha256(data).hexdigest()
                zf.writestr(f"artifacts/{clean_name}.sha256", f"{art_hash}  {clean_name}\n")
                
    return buf.getvalue()


def import_case_package(zip_bytes: bytes) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, bytes]]:
    """Unpack and verify an exported case archive."""
    buf = io.BytesIO(zip_bytes)
    
    with zipfile.ZipFile(buf, "r") as zf:
        file_list = zf.namelist()
        if "manifest.json" not in file_list:
            raise ValueError("Invalid case archive: manifest.json is missing.")
            
        manifest_data = zf.read("manifest.json")
        
        # Verify checksum if present
        if "checksum.sha256" in file_list:
            expected_line = zf.read("checksum.sha256").decode("utf-8").strip()
            expected_hash = expected_line.split()[0]
            actual_hash = hashlib.sha256(manifest_data).hexdigest()
            if expected_hash != actual_hash:
                raise ValueError(f"Integrity check failed: manifest SHA256 mismatch ({actual_hash} != {expected_hash})")
                
        manifest = json.loads(manifest_data.decode("utf-8"))
        case_dict = manifest.get("case", {})
        evidence_list = manifest.get("evidence", [])
        
        artifacts_map: dict[str, bytes] = {}
        for name in file_list:
            if name.startswith("artifacts/") and not name.endswith(".sha256"):
                art_data = zf.read(name)
                art_name = os.path.basename(name)
                artifacts_map[art_name] = art_data

        return case_dict, evidence_list, artifacts_map
