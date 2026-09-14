export type ModuleCode = "VG" | "ST" | "CE";

export type CaseStatus =
  | "CREATED"
  | "ACTIVE"
  | "EVIDENCE_SUBMITTED"
  | "CONVERGENCE_COMPUTED"
  | "READY_TO_ANCHOR"
  | "ANCHORED"
  | "FILED"
  | "CLOSED";

export interface ArtifactRecord {
  artifact_id: string;
  artifact_type: "audio" | "spectrogram" | "features" | "graph" | "report" | "text";
  uri: string;
  sha256: string;
  size_bytes?: number;
}

export interface EvidenceRecord {
  evidence_id: string;
  case_id: string;
  module_id: "voiceguard" | "shadowtrace" | "chaineye";
  submitted_by?: string;
  created_by?: string;
  verdict: Record<string, any>;
  verdict_code?: string;
  confidence: number;
  confidence_tier?: "high" | "medium" | "low";
  artifacts: ArtifactRecord[];
  hash_sha256: string;
  chain_anchor?: Record<string, any> | null;
  ipfs_cid?: string | null;
  created_at?: string;
}

export interface ConvergenceSignal {
  title: string;
  body: string;
  score?: number;
  type?: string;
}

export interface CaseConvergence {
  score: number;
  signals?: ConvergenceSignal[] | Record<string, any>;
  timezone_match?: boolean;
  activity_overlap?: number;
  graph_links?: number;
  computed_at?: string;
}

export interface CaseRecord {
  caseId: string;
  rawCaseId?: string;
  complainant: string;
  modules: ModuleCode[];
  status: CaseStatus;
  threatTier: string;
  lastUpdated: string;
  reportedLoss?: string;
  txHash?: string;
  ipfsCid?: string;
  evidenceHash?: string;
  voiceVerdict?: string;
  actorHandle?: string;
  walletTarget?: string;
  convergenceScore?: number;
  evidenceCount?: number;
  evidenceList?: EvidenceRecord[];
  convergence?: CaseConvergence | null;
  auditLog?: Array<{ ts: string; actor: string; action: string; metadata?: any }>;
}

export interface MetricCardData {
  id: string;
  title: string;
  value: string | number;
  trend: string;
  trendType: "amber" | "indigo" | "crimson";
  subtext: string;
  pulseBorder?: boolean;
}

export interface AnchorEvent {
  id: string;
  caseId: string;
  moduleName: "VoiceGuard" | "ShadowTrace" | "ChainEye";
  txHash: string;
  timestamp: string;
  blockNumber?: number;
  verified: boolean;
}

export interface ModuleStatusRecord {
  name: "VoiceGuard" | "ShadowTrace" | "ChainEye";
  code: ModuleCode;
  status: "Operational" | "Processing" | "Degraded" | "Offline";
  statusColor: "green" | "amber" | "crimson";
  metric: string;
  activeTask?: string;
}

export interface UserRecord {
  id: string;
  username: string;
  email: string;
  role: "INVESTIGATOR" | "SUPERVISOR" | "OWNER";
  created_at?: string;
  active: boolean;
}
