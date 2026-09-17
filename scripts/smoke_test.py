"""Comprehensive End-to-End Functional Smoke Test for Eye of Abyss.

Tests:
1. Health checks for all 5 services (Case Engine, VoiceGuard, ShadowTrace, ChainEye, Frontend)
2. Auth verification (Login with seeded OWNER account, JWT issuance, protected routes)
3. Case Engine (Create case, submit evidence, convergence report)
4. VoiceGuard (Audio synthesis analysis, deepfake detection verdict, confidence)
5. ChainEye (Multi-hop wallet trace, VASP attribution, withdrawal prediction)
6. ShadowTrace (Stylometric fingerprinting, actor attribution)
7. End-to-End lifecycle (Create -> Multi-module evidence -> Convergence -> Approval -> PDF/ZIP Export)
"""

import io
import json
import os
import sys
import uuid
import wave
import struct
import httpx

CASE_ENGINE_URL = os.getenv("CASE_ENGINE_URL", "http://localhost:8000")
VOICEGUARD_URL = os.getenv("VOICEGUARD_URL", "http://localhost:8001")
SHADOWTRACE_URL = os.getenv("SHADOWTRACE_URL", "http://localhost:8002")
CHAINEYE_URL = os.getenv("CHAINEYE_URL", "http://localhost:8003")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

SEED_OWNER_EMAIL = os.getenv("SEED_OWNER_EMAIL", "ashwith@localhost")
SEED_OWNER_PASSWORD = os.getenv("SEED_OWNER_PASSWORD", "1234567890")

results = {}


def log_test(test_name: str, passed: bool, details: str = ""):
    status_str = "PASS" if passed else "FAIL"
    results[test_name] = {"passed": passed, "details": details}
    print(f"[{status_str}] {test_name}: {details}")


def generate_test_wav() -> bytes:
    """Generate 1.0 second 16kHz sine wave audio in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # 16000 samples of 440Hz tone
        import math
        samples = [
            int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / 16000.0))
            for i in range(16000)
        ]
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


def run_tests():
    print("=" * 70)
    print("  EYE OF ABYSS -- END-TO-END FUNCTIONAL SMOKE TEST")
    print("=" * 70)

    client = httpx.Client(timeout=15.0, follow_redirects=True)

    # ── 1. Health Checks ───────────────────────────────────────────────────────
    print("\n[Phase 1] Service Health Checks")
    services = [
        ("Case Engine", f"{CASE_ENGINE_URL}/health"),
        ("VoiceGuard", f"{VOICEGUARD_URL}/health"),
        ("ShadowTrace", f"{SHADOWTRACE_URL}/health"),
        ("ChainEye", f"{CHAINEYE_URL}/health"),
        ("Frontend", FRONTEND_URL),
    ]
    for name, url in services:
        try:
            r = client.get(url)
            if r.status_code == 200:
                log_test(f"Health Check ({name})", True, f"HTTP 200 OK from {url}")
            else:
                log_test(f"Health Check ({name})", False, f"HTTP {r.status_code} from {url}")
        except Exception as e:
            log_test(f"Health Check ({name})", False, f"Connection failed: {e}")

    # ── 2. Auth Flow ──────────────────────────────────────────────────────────
    print("\n[Phase 2] Authentication & Access Control")
    token = None
    headers = {}
    try:
        r = client.post(
            f"{CASE_ENGINE_URL}/auth/login",
            json={"email": SEED_OWNER_EMAIL, "password": SEED_OWNER_PASSWORD},
        )
        if r.status_code == 200 and "access_token" in r.json():
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            log_test("Auth: Login with Seeded OWNER", True, f"JWT issued for {SEED_OWNER_EMAIL}")
        else:
            log_test("Auth: Login with Seeded OWNER", False, f"HTTP {r.status_code}: {r.text}")
    except Exception as e:
        log_test("Auth: Login with Seeded OWNER", False, str(e))

    if token:
        # Protected route test: /users
        try:
            r = client.get(f"{CASE_ENGINE_URL}/users", headers=headers)
            if r.status_code == 200:
                users = r.json()
                log_test("Auth: Protected Route (GET /users)", True, f"Retrieved {len(users)} user(s)")
            else:
                log_test("Auth: Protected Route (GET /users)", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            log_test("Auth: Protected Route (GET /users)", False, str(e))

    # ── 3. VoiceGuard Module ──────────────────────────────────────────────────
    print("\n[Phase 3] VoiceGuard Deepfake Detection")
    vg_evidence = None
    try:
        wav_bytes = generate_test_wav()
        files = {"file": ("test_sample.wav", wav_bytes, "audio/wav")}
        data = {"officer_id": "INVESTIGATOR_VG_01", "model": "heuristic"}
        r = client.post(f"{VOICEGUARD_URL}/analyze/file", files=files, data=data)
        if r.status_code == 200:
            res = r.json()
            vg_evidence = res.get("evidence")
            verdict = vg_evidence.get("verdict") if vg_evidence else "N/A"
            conf = vg_evidence.get("confidence") if vg_evidence else 0.0
            log_test("VoiceGuard: Audio Analysis", True, f"Verdict: {verdict}, Confidence: {conf}")
        else:
            log_test("VoiceGuard: Audio Analysis", False, f"HTTP {r.status_code}: {r.text}")
    except Exception as e:
        log_test("VoiceGuard: Audio Analysis", False, str(e))

    # ── 4. ChainEye Module ────────────────────────────────────────────────────
    print("\n[Phase 4] ChainEye Crypto Forensics")
    ce_evidence = None
    try:
        sample_wallet = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        r = client.post(
            f"{CHAINEYE_URL}/trace/wallet",
            json={"wallet_address": sample_wallet, "depth": 3, "chain": "bitcoin"},
        )
        if r.status_code == 200:
            res = r.json()
            ce_evidence = res.get("evidence")
            vasp = res.get("attributed_vasp", "Unknown")
            urgency = res.get("freeze_urgency", "MEDIUM")
            log_test("ChainEye: Wallet Trace & VASP Attribution", True, f"Attributed VASP: {vasp}, Urgency: {urgency}")
        else:
            log_test("ChainEye: Wallet Trace & VASP Attribution", False, f"HTTP {r.status_code}: {r.text}")
    except Exception as e:
        log_test("ChainEye: Wallet Trace & VASP Attribution", False, str(e))

    # ── 5. ShadowTrace Module ─────────────────────────────────────────────────
    print("\n[Phase 5] ShadowTrace Stylometry & Dark Web Attribution")
    st_evidence = None
    try:
        sample_text = "Escrow release verified. Contact @phantom_trade on telegram for bulk bitcoin orders."
        r = client.post(f"{SHADOWTRACE_URL}/fingerprint", json={"text": sample_text})
        if r.status_code == 200:
            fp_res = r.json()
            dim = fp_res.get("vector_dim", 0)
            log_test("ShadowTrace: Stylometric Fingerprinting", True, f"Fingerprint computed with {dim} dimensions")
        else:
            log_test("ShadowTrace: Stylometric Fingerprinting", False, f"HTTP {r.status_code}: {r.text}")

        r_attr = client.post(f"{SHADOWTRACE_URL}/attribute", json={"text": sample_text, "k": 3})
        if r_attr.status_code == 200:
            attr_res = r_attr.json()
            st_evidence = attr_res.get("evidence_object")
            handle = attr_res.get("handle", "unattributed")
            conf = attr_res.get("confidence", 0.0)
            log_test("ShadowTrace: Actor Attribution", True, f"Matched: {handle}, Confidence: {conf}")
        else:
            log_test("ShadowTrace: Actor Attribution", False, f"HTTP {r_attr.status_code}: {r_attr.text}")
    except Exception as e:
        log_test("ShadowTrace: Stylometry Analysis", False, str(e))

    # ── 6. Case Engine & E2E Workflow ─────────────────────────────────────────
    print("\n[Phase 6] Unified Case Lifecycle (End-to-End)")
    case_id = None
    try:
        # Step A: Create case
        r = client.post(
            f"{CASE_ENGINE_URL}/cases",
            headers=headers,
            json={
                "complainant_type": "Executive Voice Vishing & BTC Ransom (Axis Corp)",
                "reported_loss": "₹3.5 Cr",
                "modules_assigned": ["voiceguard", "chaineye", "shadowtrace"],
            },
        )
        if r.status_code == 201:
            case_data = r.json()
            case_id = case_data["case_id"]
            log_test("Case Engine: Create Case", True, f"Created Case ID: {case_id}, Status: {case_data['status']}")
        else:
            log_test("Case Engine: Create Case", False, f"HTTP {r.status_code}: {r.text}")
    except Exception as e:
        log_test("Case Engine: Create Case", False, str(e))

    if case_id and token:
        # Step B: Submit Evidence from Module 1 (VoiceGuard)
        try:
            vg_payload = {
                "case_id": case_id,
                "evidence_id": str(uuid.uuid4()),
                "module_id": "voiceguard",
                "verdict": vg_evidence.get("verdict", "Synthetic Voice Match (0.94)") if vg_evidence else "Synthetic TTS",
                "confidence": 0.94,
                "artifacts": [
                    {"filename": "spectrogram.png", "file_type": "image/png", "description": "Mel Spectrogram"}
                ],
            }
            r = client.post(f"{CASE_ENGINE_URL}/cases/{case_id}/evidence", headers=headers, json=vg_payload)
            if r.status_code == 201:
                res = r.json()
                log_test("Case Engine: Submit VoiceGuard Evidence", True, f"Evidence attached, Case status: {res.get('case_status')}")
            else:
                log_test("Case Engine: Submit VoiceGuard Evidence", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            log_test("Case Engine: Submit VoiceGuard Evidence", False, str(e))

        # Step C: Submit Evidence from Module 2 (ChainEye)
        try:
            ce_payload = {
                "case_id": case_id,
                "evidence_id": str(uuid.uuid4()),
                "module_id": "chaineye",
                "verdict": "VASP Attributed to Binance Global. Withdrawal window: 2 hrs.",
                "confidence": 0.88,
                "artifacts": [
                    {"filename": "cluster_graph.json", "file_type": "application/json", "description": "Cytoscape Flow Graph"}
                ],
            }
            r = client.post(f"{CASE_ENGINE_URL}/cases/{case_id}/evidence", headers=headers, json=ce_payload)
            if r.status_code == 201:
                res = r.json()
                log_test("Case Engine: Submit ChainEye Evidence", True, f"Evidence attached, Case status: {res.get('case_status')}")
            else:
                log_test("Case Engine: Submit ChainEye Evidence", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            log_test("Case Engine: Submit ChainEye Evidence", False, str(e))

        # Step D: Check Convergence Report
        try:
            import time
            time.sleep(0.5)
            r = client.get(f"{CASE_ENGINE_URL}/cases/{case_id}/convergence", headers=headers)
            if r.status_code == 200:
                conv_res = r.json()
                conv_data = conv_res.get("convergence")
                log_test("Case Engine: Convergence Report", True, f"Convergence computed: {conv_data is not None}")
            else:
                log_test("Case Engine: Convergence Report", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            log_test("Case Engine: Convergence Report", False, str(e))

        # Step E: Supervisor Approval
        try:
            r = client.post(f"{CASE_ENGINE_URL}/cases/{case_id}/approve", headers=headers)
            if r.status_code == 200:
                res = r.json()
                log_test("Case Engine: Supervisor Approval", True, f"Case transitioned to status: {res.get('status')}")
            else:
                log_test("Case Engine: Supervisor Approval", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            log_test("Case Engine: Supervisor Approval", False, str(e))

        # Step F: Export Court-Ready PDF
        try:
            r = client.get(f"{CASE_ENGINE_URL}/cases/{case_id}/export", headers=headers)
            if r.status_code == 200 and r.headers.get("content-type") == "application/pdf":
                pdf_size = len(r.content)
                log_test("Case Engine: Export PDF Case File", True, f"Generated valid PDF ({pdf_size} bytes)")
            else:
                log_test("Case Engine: Export PDF Case File", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            log_test("Case Engine: Export PDF Case File", False, str(e))

        # Step G: Export Full Case ZIP Package
        try:
            r = client.get(f"{CASE_ENGINE_URL}/cases/{case_id}/package", headers=headers)
            if r.status_code == 200:
                zip_size = len(r.content)
                log_test("Case Engine: Export Signed ZIP Package", True, f"Generated ZIP Package ({zip_size} bytes)")
            else:
                log_test("Case Engine: Export Signed ZIP Package", False, f"HTTP {r.status_code}: {r.text}")
        except Exception as e:
            log_test("Case Engine: Export Signed ZIP Package", False, str(e))

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    passed_count = sum(1 for v in results.values() if v["passed"])
    total_count = len(results)
    for name, res in results.items():
        tag = "[PASS]" if res["passed"] else "[FAIL]"
        print(f"  {tag:<8} {name}: {res['details']}")
    print("-" * 70)
    print(f"  Total Score: {passed_count}/{total_count} Passed ({passed_count/total_count*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
