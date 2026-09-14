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

export interface CaseRecord {
  caseId: string;
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
