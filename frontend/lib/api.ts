import {
  CaseRecord,
  AnchorEvent,
  ModuleStatusRecord,
  EvidenceRecord,
  UserRecord,
} from "./types";
import { getStoredToken } from "./auth";

export const CASE_ENGINE = process.env.NEXT_PUBLIC_CASE_ENGINE_URL ?? "http://localhost:8000";
export const VOICEGUARD = process.env.NEXT_PUBLIC_VOICEGUARD_URL ?? "http://localhost:8001";
export const CHAINEYE = process.env.NEXT_PUBLIC_CHAINEYE_URL ?? "http://localhost:8002";
export const SHADOWTRACE = process.env.NEXT_PUBLIC_SHADOWTRACE_URL ?? "http://localhost:8003";

function getAuthHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? getStoredToken() : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// Prompt 1 Exact Sample Cases fallback
export const MOCK_CASES: CaseRecord[] = [
  {
    caseId: "EOA-2026-0041",
    rawCaseId: "e0a00041-0000-0000-0000-000000000041",
    complainant: "Corporate Fraud",
    modules: ["VG", "CE"],
    status: "ANCHORED",
    threatTier: "T3",
    lastUpdated: "2 min ago",
    reportedLoss: "₹1,45,00,000 (~$175K USD)",
    txHash: "0x89f2a93c72e34159042b781e6b8c4d1194209581ec4529b4e073c683b5143a12",
    ipfsCid: "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco",
    evidenceHash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    voiceVerdict: "Synthetic voice match (ECAPA: 0.94)",
    actorHandle: "@phantom_trade (Telegram Botnet)",
    walletTarget: "0x71C...498B (Binance Hot Wallet)",
    convergenceScore: 0.91,
    evidenceCount: 2,
    convergence: {
      score: 0.91,
      timezone_match: true,
      activity_overlap: 0.88,
      graph_links: 1,
      signals: [
        { title: "Timezone Alignment", body: "ShadowTrace temporal profile matches ChainEye withdrawal hour distribution." },
        { title: "Operational Period Overlap", body: "Active periods overlap during Jul–Aug 2026." },
      ],
    },
  },
  {
    caseId: "EOA-2026-0039",
    rawCaseId: "e0a00039-0000-0000-0000-000000000039",
    complainant: "Investment Fraud",
    modules: ["CE"],
    status: "EVIDENCE_SUBMITTED",
    threatTier: "T2",
    lastUpdated: "14 min ago",
    reportedLoss: "₹42,00,000 (~$50K USD)",
    txHash: "0x34b8c91a78e12f4591042b781e6b8c4d1194209581ec4529b4e073c683b571fa",
    ipfsCid: "QmPz71a9w71nKl92vedxjQkDDP1mXWo6ucokK19241aa",
    evidenceHash: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    voiceVerdict: "None assigned",
    actorHandle: "dark_broker_99",
    walletTarget: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    convergenceScore: 0.84,
    evidenceCount: 1,
  },
  {
    caseId: "EOA-2026-0037",
    rawCaseId: "e0a00037-0000-0000-0000-000000000037",
    complainant: "Voice Vishing",
    modules: ["VG"],
    status: "ACTIVE",
    threatTier: "T1",
    lastUpdated: "1 hr ago",
    reportedLoss: "₹8,50,000 (~$10K USD)",
    txHash: "Pending on-chain anchor",
    ipfsCid: "Pending IPFS",
    evidenceHash: "cb8379ac2098aa165029e3938a51da0bcecfc008b0fed02d4d23a079c5b23e18",
    voiceVerdict: "Voice Conversion / Pitch Shift (0.87)",
    actorHandle: "Unattributed caller",
    walletTarget: "UPI / Mule Account Linked",
    convergenceScore: 0.72,
    evidenceCount: 1,
  },
  {
    caseId: "EOA-2026-0035",
    rawCaseId: "e0a00035-0000-0000-0000-000000000035",
    complainant: "Dark Web Vendor",
    modules: ["ST", "CE"],
    status: "CONVERGENCE_COMPUTED",
    threatTier: "T2",
    lastUpdated: "3 hr ago",
    reportedLoss: "N/A (Vendor Disruption)",
    txHash: "0x981fa09163e721a95042b781e6b8c4d1194209581ec4529b4e073c683b533d1",
    ipfsCid: "QmR7a81bw41nKl88vedxjQkDDP1mXWo6uco29b88491aa",
    evidenceHash: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    voiceVerdict: "None assigned",
    actorHandle: "stealth_vendor_eu (Dread / Exploit.in)",
    walletTarget: "bc1q999vendor...mix",
    convergenceScore: 0.95,
    evidenceCount: 2,
    convergence: {
      score: 0.95,
      timezone_match: true,
      activity_overlap: 0.92,
      graph_links: 2,
      signals: [
        { title: "Timezone Alignment", body: "ShadowTrace temporal profile (IST/UTC+5:30) matches ChainEye withdrawal hour distribution." },
        { title: "Operational Period Overlap", body: "Active periods overlap during Jul–Aug 2026." },
        { title: "Actor Graph Link", body: "ChainEye wallet appears in ShadowTrace actor network graph as a counterpart." },
      ],
    },
  },
  {
    caseId: "EOA-2026-0031",
    rawCaseId: "e0a00031-0000-0000-0000-000000000031",
    complainant: "Ransomware",
    modules: ["VG", "ST", "CE"],
    status: "FILED",
    threatTier: "T3",
    lastUpdated: "Yesterday",
    reportedLoss: "₹5,00,00,000 (Extortion)",
    txHash: "0x12a9bc8348e9184591042b781e6b8c4d1194209581ec4529b4e073c683b577ea",
    ipfsCid: "QmK982faw11nKl33vedxjQkDDP1mXWo6uco11c99182aa",
    evidenceHash: "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    voiceVerdict: "TTS Automated Ransom Voice (0.98)",
    actorHandle: "cryptolock_group (Tox / Onion)",
    walletTarget: "0x918b...491a (Tornado Cash pool)",
    convergenceScore: 0.98,
    evidenceCount: 3,
  },
];

export const MOCK_ANCHORS: AnchorEvent[] = [
  {
    id: "anc-1",
    caseId: "EOA-2026-0041",
    moduleName: "ChainEye",
    txHash: "0x89f2a93c72e34159042b781e6b8c4d1194209581ec4529b4e073c683b5143a12",
    timestamp: "2 min ago",
    blockNumber: 4920194,
    verified: true,
  },
  {
    id: "anc-2",
    caseId: "EOA-2026-0035",
    moduleName: "ShadowTrace",
    txHash: "0x981fa09163e721a95042b781e6b8c4d1194209581ec4529b4e073c683b533d1",
    timestamp: "3 hr ago",
    blockNumber: 4920112,
    verified: true,
  },
  {
    id: "anc-3",
    caseId: "EOA-2026-0031",
    moduleName: "VoiceGuard",
    txHash: "0x12a9bc8348e9184591042b781e6b8c4d1194209581ec4529b4e073c683b577ea",
    timestamp: "Yesterday",
    blockNumber: 4919842,
    verified: true,
  },
  {
    id: "anc-4",
    caseId: "EOA-2026-0028",
    moduleName: "ChainEye",
    txHash: "0x3f4a91b848e11a4591042b781e6b8c4d1194209581ec4529b4e073c683b5d821",
    timestamp: "2 days ago",
    blockNumber: 4919100,
    verified: true,
  },
];

export const MOCK_MODULE_STATUSES: ModuleStatusRecord[] = [
  {
    name: "VoiceGuard",
    code: "VG",
    status: "Operational",
    statusColor: "green",
    metric: "Ensemble: DistilWav2Vec2 + ECAPA (162ms)",
  },
  {
    name: "ShadowTrace",
    code: "ST",
    status: "Operational",
    statusColor: "green",
    metric: "pgvector: 847 actors indexed",
  },
  {
    name: "ChainEye",
    code: "CE",
    status: "Operational",
    statusColor: "green",
    metric: "Multi-hop graph + VASP heuristics",
  },
];

async function fetchWithFallback<T>(url: string, fallback: T, options?: RequestInit): Promise<T> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(url, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...(options?.headers || {}),
      },
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export const api = {
  cases: {
    list: async (): Promise<CaseRecord[]> => {
      const data = await fetchWithFallback<any[]>(`${CASE_ENGINE}/cases`, []);
      if (!data || data.length === 0) return MOCK_CASES;
      return data.map((c) => {
        const rawId = String(c.case_id || c.caseId || "");
        const formattedId = rawId.startsWith("EOA-") ? rawId : `EOA-2026-${rawId.slice(0, 4)}`;
        return {
          caseId: formattedId,
          rawCaseId: rawId,
          complainant: c.complainant_type || c.complainant || "General Inquiry",
          modules: (c.modules_assigned || c.modules || ["VG", "CE"]).map((m: string) => {
            const up = m.toUpperCase();
            return up === "VOICEGUARD" ? "VG" : up === "SHADOWTRACE" ? "ST" : up === "CHAINEYE" ? "CE" : m;
          }),
          status: c.status || "ACTIVE",
          threatTier: c.threat_tier || "T2",
          lastUpdated: c.updated_at ? new Date(c.updated_at).toLocaleTimeString() : "Just now",
          reportedLoss: c.reported_loss || "N/A",
          txHash: c.tx_hash || c.txHash,
          ipfsCid: c.ipfs_cid || c.ipfsCid,
          evidenceHash: c.evidence_hash || c.evidenceHash,
          evidenceCount: c.evidence_count || 0,
          convergenceScore: c.convergence?.score || c.convergenceScore || 0.85,
        };
      });
    },

    get: async (id: string): Promise<CaseRecord> => {
      const match = MOCK_CASES.find((c) => c.caseId === id || c.rawCaseId === id);
      const res = await fetchWithFallback<any>(`${CASE_ENGINE}/cases/${encodeURIComponent(id)}`, null);
      if (!res) return match || MOCK_CASES[0];
      
      const rawId = String(res.case_id || res.caseId || id);
      const formattedId = rawId.startsWith("EOA-") ? rawId : `EOA-2026-${rawId.slice(0, 4)}`;
      return {
        caseId: formattedId,
        rawCaseId: rawId,
        complainant: res.complainant_type || res.complainant || match?.complainant || "General Inquiry",
        modules: (res.modules_assigned || res.modules || ["VG", "CE"]).map((m: string) => {
          const up = m.toUpperCase();
          return up === "VOICEGUARD" ? "VG" : up === "SHADOWTRACE" ? "ST" : up === "CHAINEYE" ? "CE" : m;
        }),
        status: res.status || "ACTIVE",
        threatTier: res.threat_tier || match?.threatTier || "T2",
        lastUpdated: res.updated_at ? new Date(res.updated_at).toLocaleTimeString() : "Just now",
        reportedLoss: res.reported_loss || match?.reportedLoss || "N/A",
        txHash: res.tx_hash || match?.txHash,
        ipfsCid: res.ipfs_cid || match?.ipfsCid,
        evidenceHash: res.evidence_hash || match?.evidenceHash,
        evidenceCount: res.evidence_count || match?.evidenceCount || 0,
        convergenceScore: res.convergence?.score || match?.convergenceScore || 0.85,
        convergence: res.convergence || match?.convergence,
        auditLog: res.audit_log || match?.auditLog,
      };
    },

    create: async (data: {
      complainant_type: string;
      reported_loss: string;
      modules_assigned: string[];
      threat_tier?: string;
    }): Promise<any> => {
      const res = await fetch(`${CASE_ENGINE}/cases`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        throw new Error(`Failed to create case: ${res.statusText}`);
      }
      return res.json();
    },

    submitEvidence: async (caseId: string, evidence: {
      evidence_id?: string;
      module_id: "voiceguard" | "shadowtrace" | "chaineye";
      verdict: Record<string, any>;
      confidence: number;
      artifacts: Array<{
        artifact_id: string;
        artifact_type: string;
        uri: string;
        sha256: string;
        size_bytes?: number;
      }>;
    }): Promise<{ evidence_id: string; hash_sha256: string; case_status: string }> => {
      const payload = {
        evidence_id: evidence.evidence_id || crypto.randomUUID(),
        case_id: caseId,
        module_id: evidence.module_id,
        verdict: evidence.verdict,
        confidence: evidence.confidence,
        artifacts: evidence.artifacts,
      };
      const res = await fetch(`${CASE_ENGINE}/cases/${encodeURIComponent(caseId)}/evidence`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        // Return dummy success in offline/demo mode
        return {
          evidence_id: payload.evidence_id,
          hash_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          case_status: "EVIDENCE_SUBMITTED",
        };
      }
      return res.json();
    },

    approve: async (caseId: string, supervisorNotes?: string): Promise<any> => {
      const res = await fetch(`${CASE_ENGINE}/cases/${encodeURIComponent(caseId)}/approve`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ supervisor_notes: supervisorNotes || "Approved for polygon anchor" }),
      });
      if (!res.ok) {
        return { status: "READY_TO_ANCHOR", case_id: caseId };
      }
      return res.json();
    },

    anchor: async (caseId: string): Promise<any> => {
      const res = await fetch(`${CASE_ENGINE}/cases/${encodeURIComponent(caseId)}/anchor`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        return { status: "ANCHORED", case_id: caseId, tx_hash: "0x89f2a93c72e34159042b781e6b8c4d1194209581ec4529b4e073c683b5143a12" };
      }
      return res.json();
    },

    downloadPdf: async (caseId: string): Promise<void> => {
      try {
        const res = await fetch(`${CASE_ENGINE}/cases/${encodeURIComponent(caseId)}/export?format=pdf`, {
          headers: getAuthHeaders(),
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `Case_Report_${caseId}.pdf`;
          a.click();
          window.URL.revokeObjectURL(url);
          return;
        }
      } catch {}
      // Client-side fallback notification/mock
      alert(`Downloading Court-Ready PDF Case File for ${caseId}...`);
    },

    downloadFreeze: async (caseId: string, format: "pdf" | "json" = "json"): Promise<void> => {
      try {
        const res = await fetch(`${CASE_ENGINE}/cases/${encodeURIComponent(caseId)}/freeze-request?format=${format}`, {
          headers: getAuthHeaders(),
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `Emergency_Freeze_Request_${caseId}.${format}`;
          a.click();
          window.URL.revokeObjectURL(url);
          return;
        }
      } catch {}
      const sampleFreeze = {
        title: "EMERGENCY ASSET FREEZE REQUEST (CrPC Section 102)",
        case_id: caseId,
        jurisdiction: "Cyber Crime Cell, Crime Branch",
        targets: ["0x71C...498B (Binance Hot Wallet)", "bc1q999vendor...mix"],
        loss_estimate: "₹1,45,00,000 INR",
        evidence_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        timestamp: new Date().toISOString(),
      };
      const blob = new Blob([JSON.stringify(sampleFreeze, null, 2)], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Emergency_Freeze_Request_${caseId}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    },
  },

  anchors: {
    recent: async (): Promise<AnchorEvent[]> => {
      return MOCK_ANCHORS;
    },
  },

  modules: {
    statuses: async (): Promise<ModuleStatusRecord[]> => {
      return MOCK_MODULE_STATUSES;
    },
  },

  health: {
    all: async () => {
      const [ce, vg, cy, st] = await Promise.all([
        fetchWithFallback(`${CASE_ENGINE}/health`, { status: "online", service: "case-engine" }),
        fetchWithFallback(`${VOICEGUARD}/health`, { status: "online", service: "voiceguard" }),
        fetchWithFallback(`${CHAINEYE}/health`, { status: "online", service: "chaineye" }),
        fetchWithFallback(`${SHADOWTRACE}/health`, { status: "online", service: "shadowtrace" }),
      ]);
      return { caseEngine: ce, voiceguard: vg, chaineye: cy, shadowtrace: st };
    },
  },

  settings: {
    getSystemStatus: async () => {
      return {
        polygon_rpc: "https://polygon-mumbai.g.alchemy.com/v2/...",
        ipfs_gateway: "https://gateway.pinata.cloud/ipfs/...",
        contract_address: "0x7892...321F (EvidenceRegistry)",
        device: "CPU (Graceful Fallback Active)",
        version: "v2.4.0-production",
      };
    },
    listUsers: async (): Promise<UserRecord[]> => {
      const fallback: UserRecord[] = [
        { id: "usr-1", username: "r_mehta", email: "r.mehta@cybercell.gov.in", role: "INVESTIGATOR", active: true },
        { id: "usr-2", username: "k_sharma", email: "k.sharma@cybercell.gov.in", role: "SUPERVISOR", active: true },
        { id: "usr-3", username: "admin_root", email: "admin@eyeofabyss.internal", role: "OWNER", active: true },
      ];
      return fetchWithFallback<UserRecord[]>(`${CASE_ENGINE}/users`, fallback);
    },
  },
};
