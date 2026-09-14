import { CaseRecord, AnchorEvent, ModuleStatusRecord } from "./types";

const CASE_ENGINE = process.env.NEXT_PUBLIC_CASE_ENGINE_URL ?? "http://localhost:8000";
const VOICEGUARD = process.env.NEXT_PUBLIC_VOICEGUARD_URL ?? "http://localhost:8001";
const SHADOWTRACE = process.env.NEXT_PUBLIC_SHADOWTRACE_URL ?? "http://localhost:8002";
const CHAINEYE = process.env.NEXT_PUBLIC_CHAINEYE_URL ?? "http://localhost:8003";

// Prompt 1 Exact Sample Cases
export const MOCK_CASES: CaseRecord[] = [
  {
    caseId: "EOA-2026-0041",
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
  },
  {
    caseId: "EOA-2026-0039",
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
  },
  {
    caseId: "EOA-2026-0037",
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
  },
  {
    caseId: "EOA-2026-0035",
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
  },
  {
    caseId: "EOA-2026-0031",
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
  },
];

// Prompt 1 Exact Sample Anchors
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

// Prompt 1 Exact Module Statuses
export const MOCK_MODULE_STATUSES: ModuleStatusRecord[] = [
  {
    name: "VoiceGuard",
    code: "VG",
    status: "Operational",
    statusColor: "green",
    metric: "Avg latency 148ms",
  },
  {
    name: "ShadowTrace",
    code: "ST",
    status: "Operational",
    statusColor: "green",
    metric: "Corpus: 847 actors",
  },
  {
    name: "ChainEye",
    code: "CE",
    status: "Processing",
    statusColor: "amber",
    metric: "EOA-2026-0041 — trace in progress",
  },
];

async function fetchWithFallback<T>(url: string, fallback: T): Promise<T> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1200);
    const res = await fetch(url, { signal: controller.signal });
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
      return data.map((c) => ({
        caseId: c.case_id ? `EOA-${c.case_id.slice(0, 8)}` : c.caseId,
        complainant: c.complainant_type || c.complainant || "Unknown",
        modules: c.modules_assigned || c.modules || ["VG", "CE"],
        status: c.status || "ACTIVE",
        threatTier: c.threat_tier || "T2",
        lastUpdated: "Just now",
        reportedLoss: c.reported_loss || "N/A",
      }));
    },
    get: async (id: string): Promise<CaseRecord | null> => {
      const match = MOCK_CASES.find((c) => c.caseId === id);
      return fetchWithFallback(`${CASE_ENGINE}/cases/${id}`, match || MOCK_CASES[0]);
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
      const [ce, vg, st, cy] = await Promise.all([
        fetchWithFallback(`${CASE_ENGINE}/health`, { status: "offline" }),
        fetchWithFallback(`${VOICEGUARD}/health`, { status: "offline" }),
        fetchWithFallback(`${SHADOWTRACE}/health`, { status: "offline" }),
        fetchWithFallback(`${CHAINEYE}/health`, { status: "offline" }),
      ]);
      return { caseEngine: ce, voiceguard: vg, shadowtrace: st, chaineye: cy };
    },
  },
};
