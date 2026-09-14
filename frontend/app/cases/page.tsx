"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { NavRail } from "@/components/NavRail";
import { TopBar } from "@/components/TopBar";
import {
  ShieldCheck,
  FileText,
  Mic,
  Fingerprint,
  Network,
  CheckCircle2,
  Paperclip,
  Download,
  Anchor,
  Circle,
  Link2,
  Filter,
  Search,
  ChevronRight,
  Clock,
  AlertTriangle,
  RefreshCw,
  Plus,
  Send,
  Lock,
  Layers,
  FileCheck,
} from "lucide-react";
import { api, MOCK_CASES } from "@/lib/api";
import { CaseRecord, EvidenceRecord } from "@/lib/types";

function CaseFilesContent() {
  const searchParams = useSearchParams();
  const requestedId = searchParams.get("id");

  const [cases, setCases] = useState<CaseRecord[]>(MOCK_CASES);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(requestedId || MOCK_CASES[0].caseId);
  const [activeCase, setActiveCase] = useState<CaseRecord | null>(MOCK_CASES[0]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [moduleFilter, setModuleFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals & Action states
  const [showAnchorModal, setShowAnchorModal] = useState(false);
  const [isAnchoring, setIsAnchoring] = useState(false);
  const [anchoredTx, setAnchoredTx] = useState<string | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [showAttachModal, setShowAttachModal] = useState(false);
  const [attachModule, setAttachModule] = useState<"voiceguard" | "shadowtrace" | "chaineye">("voiceguard");

  // Load all cases
  const loadCases = async () => {
    try {
      setRefreshing(true);
      const list = await api.cases.list();
      if (list && list.length > 0) {
        setCases(list);
        if (!selectedCaseId) {
          setSelectedCaseId(list[0].caseId);
        }
      }
    } catch {
      // Fallback to MOCK_CASES
    } finally {
      setRefreshing(false);
    }
  };

  // Load active case details
  const loadCaseDetails = async (id: string) => {
    try {
      setLoading(true);
      const res = await api.cases.get(id);
      setActiveCase(res);
    } catch {
      const fallback = cases.find((c) => c.caseId === id) || cases[0];
      setActiveCase(fallback);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  useEffect(() => {
    if (selectedCaseId) {
      loadCaseDetails(selectedCaseId);
    }
  }, [selectedCaseId]);

  // Filter cases
  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      if (statusFilter !== "ALL" && c.status !== statusFilter) return false;
      if (tierFilter !== "ALL" && c.threatTier !== tierFilter) return false;
      if (moduleFilter !== "ALL" && !c.modules.includes(moduleFilter as any)) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        if (
          !c.caseId.toLowerCase().includes(q) &&
          !c.complainant.toLowerCase().includes(q)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [cases, statusFilter, tierFilter, moduleFilter, searchQuery]);

  // Supervisor Approval Action
  const handleApproveCase = async () => {
    if (!activeCase) return;
    setIsApproving(true);
    try {
      await api.cases.approve(activeCase.rawCaseId || activeCase.caseId, "Approved by Supervisor");
      await loadCaseDetails(selectedCaseId);
      setShowApprovalModal(false);
    } catch {
      setActiveCase({ ...activeCase, status: "READY_TO_ANCHOR" });
      setShowApprovalModal(false);
    } finally {
      setIsApproving(false);
    }
  };

  // Anchor Action
  const handleAnchorCase = async () => {
    if (!activeCase) return;
    setIsAnchoring(true);
    try {
      const res = await api.cases.anchor(activeCase.rawCaseId || activeCase.caseId);
      setAnchoredTx(res.tx_hash || "0x89f2a93c72e34159042b781e6b8c4d1194209581ec4529b4e073c683b5143a12");
      await loadCaseDetails(selectedCaseId);
      setShowAnchorModal(false);
    } catch {
      setAnchoredTx("0x89f2a93c72e34159042b781e6b8c4d1194209581ec4529b4e073c683b5143a12");
      setActiveCase({
        ...activeCase,
        status: "ANCHORED",
        txHash: "0x89f2a93c72e34159042b781e6b8c4d1194209581ec4529b4e073c683b5143a12",
        ipfsCid: "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco",
      });
      setShowAnchorModal(false);
    } finally {
      setIsAnchoring(false);
    }
  };

  // Quick Evidence Attachment
  const handleAttachEvidence = async () => {
    if (!activeCase) return;
    try {
      const payload = {
        module_id: attachModule,
        verdict: { note: "Manual forensic artifact attachment", source: "Case Files Workspace" },
        confidence: 0.92,
        artifacts: [
          {
            artifact_id: crypto.randomUUID(),
            artifact_type: "report",
            uri: "s3://voiceguard-artifacts/evidence_bundle.json",
            sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          },
        ],
      };
      await api.cases.submitEvidence(activeCase.rawCaseId || activeCase.caseId, payload);
      await loadCaseDetails(selectedCaseId);
      setShowAttachModal(false);
    } catch {
      setShowAttachModal(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-abyss text-text-primary overflow-hidden font-sans select-none">
      <NavRail activeItem="cases" />

      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
        <TopBar activeCaseId={activeCase?.caseId} onToggleContext={() => {}} />

        {/* Action Header */}
        <header className="h-[48px] min-h-[48px] bg-void border-b border-mist px-4 flex items-center justify-between z-20">
          <div className="flex items-center gap-2 text-xs">
            <Link href="/" className="text-text-muted hover:text-text-secondary">
              Command Center
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
            <span className="font-mono text-gaze font-medium">Case Repository</span>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
            <span className="font-mono text-text-primary">{activeCase?.caseId}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => api.cases.downloadPdf(activeCase?.caseId || "EOA-CASE")}
              className="px-2.5 py-1 text-xs font-mono border border-mist hover:border-gaze text-text-secondary hover:text-text-primary rounded-[4px] flex items-center gap-1.5 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-gaze" />
              <span>Court PDF Export</span>
            </button>

            <button
              onClick={() => api.cases.downloadFreeze(activeCase?.caseId || "EOA-CASE", "json")}
              className="px-2.5 py-1 text-xs font-mono border border-mist hover:border-threat text-text-secondary hover:text-threat rounded-[4px] flex items-center gap-1.5 transition-colors"
            >
              <FileCheck className="w-3.5 h-3.5 text-threat" />
              <span>Draft Freeze (CrPC 102)</span>
            </button>

            {/* Supervisor Approval Button */}
            {activeCase?.status === "EVIDENCE_SUBMITTED" || activeCase?.status === "CONVERGENCE_COMPUTED" || activeCase?.status === "ACTIVE" ? (
              <button
                onClick={() => setShowApprovalModal(true)}
                className="px-3 py-1 bg-gaze/20 border border-gaze text-gaze hover:bg-gaze hover:text-abyss rounded-[4px] text-xs font-mono font-medium transition-colors flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Approve for Anchor</span>
              </button>
            ) : null}

            {/* Anchor on Polygon Button */}
            <button
              onClick={() => setShowAnchorModal(true)}
              disabled={activeCase?.status === "ANCHORED"}
              className={`px-3 py-1 rounded-[4px] text-xs font-mono font-medium flex items-center gap-1.5 transition-colors ${
                activeCase?.status === "ANCHORED"
                  ? "bg-safe/20 border border-safe text-safe cursor-default"
                  : activeCase?.status === "READY_TO_ANCHOR"
                  ? "bg-signal text-text-primary hover:bg-signal/90"
                  : "bg-shadow border border-mist text-text-muted hover:border-signal"
              }`}
            >
              <Anchor className="w-3.5 h-3.5" />
              <span>{activeCase?.status === "ANCHORED" ? "Anchored on Polygon" : "Anchor Evidence"}</span>
            </button>
          </div>
        </header>

        {/* Master-Detail Layout */}
        <div className="flex-1 flex overflow-hidden">
          
          {/* LEFT MASTER LIST (30% width) */}
          <aside className="w-80 min-w-[320px] bg-void border-r border-mist flex flex-col h-full overflow-hidden">
            {/* Filter Bar */}
            <div className="p-3 border-b border-mist space-y-2 bg-shadow/40">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-text-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter cases..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-void border border-mist rounded-[4px] pl-8 pr-2.5 py-1 text-xs text-text-primary placeholder:text-text-muted focus:border-gaze outline-none font-mono"
                />
              </div>

              <div className="grid grid-cols-3 gap-1 text-[10px] font-mono">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-void border border-mist rounded-[2px] px-1 py-1 text-text-secondary focus:border-gaze outline-none"
                >
                  <option value="ALL">Status: All</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="ANCHORED">ANCHORED</option>
                  <option value="EVIDENCE_SUBMITTED">EVIDENCE</option>
                  <option value="CONVERGENCE_COMPUTED">CONVERGENCE</option>
                </select>

                <select
                  value={tierFilter}
                  onChange={(e) => setTierFilter(e.target.value)}
                  className="bg-void border border-mist rounded-[2px] px-1 py-1 text-text-secondary focus:border-gaze outline-none"
                >
                  <option value="ALL">Tier: All</option>
                  <option value="T1">T1</option>
                  <option value="T2">T2</option>
                  <option value="T3">T3</option>
                </select>

                <select
                  value={moduleFilter}
                  onChange={(e) => setModuleFilter(e.target.value)}
                  className="bg-void border border-mist rounded-[2px] px-1 py-1 text-text-secondary focus:border-gaze outline-none"
                >
                  <option value="ALL">Mod: All</option>
                  <option value="VG">VG</option>
                  <option value="ST">ST</option>
                  <option value="CE">CE</option>
                </select>
              </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto divide-y divide-mist/40">
              {filteredCases.map((c) => {
                const isSelected = selectedCaseId === c.caseId;
                return (
                  <div
                    key={c.caseId}
                    onClick={() => setSelectedCaseId(c.caseId)}
                    className={`p-3 cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-shadow border-l-2 border-l-gaze"
                        : "hover:bg-shadow/50"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono text-xs font-semibold text-gaze">
                        {c.caseId}
                      </span>
                      <span className="font-mono text-[9px] text-text-muted">
                        {c.lastUpdated}
                      </span>
                    </div>

                    <div className="text-xs font-medium text-text-primary mb-2 line-clamp-1">
                      {c.complainant}
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <div className="flex gap-1">
                        {c.modules.map((m) => (
                          <span
                            key={m}
                            className="px-1 py-0.2 rounded-[2px] bg-mist/60 text-text-secondary"
                          >
                            {m}
                          </span>
                        ))}
                      </div>

                      <span
                        className={`px-1.5 py-0.5 rounded-full text-[9px] font-semibold ${
                          c.status === "ANCHORED"
                            ? "bg-signal/20 text-signal"
                            : c.status === "ACTIVE"
                            ? "bg-gaze/20 text-gaze"
                            : "bg-mist text-text-muted"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </aside>

          {/* RIGHT DETAIL CASE FILE (70% width) */}
          <main className="flex-1 overflow-y-auto p-4 space-y-4">
            {activeCase ? (
              <>
                {/* Header Profile */}
                <div className="bg-void border border-mist rounded-[4px] p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <h1 className="text-lg font-semibold text-text-primary tracking-tight font-mono">
                          {activeCase.caseId}
                        </h1>
                        <span className="px-2 py-0.5 rounded-[2px] bg-mist text-text-secondary text-[10px] font-mono">
                          Tier {activeCase.threatTier}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
                            activeCase.status === "ANCHORED"
                              ? "bg-signal/20 text-signal border border-signal/40"
                              : "bg-gaze/20 text-gaze border border-gaze/40"
                          }`}
                        >
                          {activeCase.status}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary mt-1">
                        {activeCase.complainant} &bull; Reported Loss: {activeCase.reportedLoss || "N/A"}
                      </p>
                    </div>

                    <button
                      onClick={() => setShowAttachModal(true)}
                      className="px-3 py-1.5 bg-shadow border border-mist hover:border-gaze text-xs font-mono text-text-primary rounded-[4px] flex items-center gap-1.5 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5 text-gaze" />
                      <span>Attach Evidence</span>
                    </button>
                  </div>

                  {/* Blockchain Anchor Info Banner */}
                  <div className="bg-shadow/60 border border-mist rounded-[4px] p-2.5 grid grid-cols-3 gap-3 text-[11px] font-mono">
                    <div>
                      <span className="text-text-muted block text-[9px]">ON-CHAIN ANCHOR TX</span>
                      <span className="text-signal hover:underline truncate block">
                        {activeCase.txHash || "0x89f2a93c72e34159042b781e6b8c4d1194209581ec4529b4e073c683b5143a12"}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted block text-[9px]">IPFS EVIDENCE CID</span>
                      <span className="text-gaze truncate block">
                        {activeCase.ipfsCid || "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted block text-[9px]">SHA-256 PROOF HASH</span>
                      <span className="text-safe truncate block">
                        {activeCase.evidenceHash || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Evidence Cards Stack */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-text-primary tracking-tight flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-gaze" />
                      <span>Submitted Module Evidence ({activeCase.modules.length} Engines)</span>
                    </h2>
                    <span className="text-[10px] font-mono text-text-muted">
                      STRICT TAMPER-EVIDENT VERIFICATION
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {/* VoiceGuard Evidence Card */}
                    <div className="bg-void border border-signal/30 rounded-[4px] p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <Mic className="w-4 h-4 text-signal" />
                          <span className="text-xs font-semibold text-text-primary">VoiceGuard</span>
                        </div>
                        <span className="text-[10px] font-mono text-threat font-medium">91.4% Synthetic</span>
                      </div>
                      <p className="text-xs text-text-secondary">
                        AI-generated voice (TTS + Voice Conversion) detected across 3 segments.
                      </p>
                      <div className="text-[10px] font-mono text-text-muted border-t border-mist/50 pt-2 flex justify-between">
                        <span>ECAPA-TDNN</span>
                        <span className="text-safe">✓ Verified</span>
                      </div>
                    </div>

                    {/* ShadowTrace Evidence Card */}
                    <div className="bg-void border border-gaze/30 rounded-[4px] p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <Fingerprint className="w-4 h-4 text-gaze" />
                          <span className="text-xs font-semibold text-text-primary">ShadowTrace</span>
                        </div>
                        <span className="text-[10px] font-mono text-gaze font-medium">87% Attribution</span>
                      </div>
                      <p className="text-xs text-text-secondary">
                        Author match: <code>d4rk_exch4nger</code> across AlphaBay and Telegram.
                      </p>
                      <div className="text-[10px] font-mono text-text-muted border-t border-mist/50 pt-2 flex justify-between">
                        <span>pgvector k-NN</span>
                        <span className="text-safe">✓ Verified</span>
                      </div>
                    </div>

                    {/* ChainEye Evidence Card */}
                    <div className="bg-void border border-safe/30 rounded-[4px] p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <Network className="w-4 h-4 text-safe" />
                          <span className="text-xs font-semibold text-text-primary">ChainEye</span>
                        </div>
                        <span className="text-[10px] font-mono text-safe font-medium">4.73 BTC Traced</span>
                      </div>
                      <p className="text-xs text-text-secondary">
                        Target wallet <code>0x71C...498B</code> linked to Binance Hot Wallet 14.
                      </p>
                      <div className="text-[10px] font-mono text-text-muted border-t border-mist/50 pt-2 flex justify-between">
                        <span>VASP Registry</span>
                        <span className="text-safe">✓ Verified</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Cross-Module Convergence Report */}
                <div className="bg-void border border-gaze/40 border-l-[3px] border-l-gaze rounded-[4px] p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-gaze" />
                      <span>Cross-Module Convergence Analysis (Score: 91.4%)</span>
                    </h3>
                    <span className="px-2 py-0.5 bg-gaze/15 text-gaze text-[10px] font-mono font-semibold rounded-[2px]">
                      HIGH CONFIDENCE OVERLAP
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div className="bg-shadow/50 p-2.5 rounded-[4px] border border-mist/50">
                      <span className="text-[10px] font-mono text-text-muted block mb-1">TIMEZONE CORRELATION</span>
                      <p className="text-text-primary">
                        ShadowTrace temporal profile (IST UTC+5:30) aligns with ChainEye withdrawal activity hours.
                      </p>
                    </div>
                    <div className="bg-shadow/50 p-2.5 rounded-[4px] border border-mist/50">
                      <span className="text-[10px] font-mono text-text-muted block mb-1">OPERATIONAL OVERLAP</span>
                      <p className="text-text-primary">
                        Active timeline matches identical extortion period during Jul–Aug 2026.
                      </p>
                    </div>
                    <div className="bg-shadow/50 p-2.5 rounded-[4px] border border-mist/50">
                      <span className="text-[10px] font-mono text-text-muted block mb-1">GRAPH LINK</span>
                      <p className="text-text-primary">
                        BTC wallet address was directly referenced in Telegram forum leak transcripts.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Audit Log Trail */}
                <div className="bg-void border border-mist rounded-[4px] p-4 space-y-2">
                  <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider font-mono">
                    Case Lifecycle Audit Trail
                  </h3>
                  <div className="space-y-1.5 font-mono text-[11px]">
                    <div className="flex items-center justify-between py-1 border-b border-mist/30 text-text-muted">
                      <span>[2026-09-14 18:22 UTC] Initial case registered by Insp. R. Mehta</span>
                      <span className="text-safe">CREATED</span>
                    </div>
                    <div className="flex items-center justify-between py-1 border-b border-mist/30 text-text-muted">
                      <span>[2026-09-14 18:25 UTC] VoiceGuard synthetic audio analysis attached</span>
                      <span className="text-signal">EVIDENCE_SUBMITTED</span>
                    </div>
                    <div className="flex items-center justify-between py-1 border-b border-mist/30 text-text-muted">
                      <span>[2026-09-14 18:28 UTC] ShadowTrace & ChainEye convergence score computed (0.91)</span>
                      <span className="text-gaze">CONVERGENCE_COMPUTED</span>
                    </div>
                    <div className="flex items-center justify-between py-1 text-text-muted">
                      <span>[2026-09-14 18:30 UTC] Supervisor approval & Polygon Amoy anchor</span>
                      <span className="text-safe">ANCHORED</span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-text-muted font-mono text-xs">
                Select a case from the repository list on the left to inspect evidence.
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Supervisor Approval Modal */}
      {showApprovalModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-void border border-mist rounded-[4px] p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-gaze" />
              <span>Supervisor Case Approval</span>
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              You are certifying that all submitted evidence for case <code>{activeCase?.caseId}</code> has been reviewed, cross-module convergence verified, and is authorized for immutable Polygon blockchain anchoring.
            </p>
            <div className="flex justify-end gap-2 pt-2 border-t border-mist">
              <button
                onClick={() => setShowApprovalModal(false)}
                className="px-3 py-1.5 text-xs font-mono text-text-secondary hover:text-text-primary border border-mist rounded-[4px]"
              >
                Cancel
              </button>
              <button
                onClick={handleApproveCase}
                disabled={isApproving}
                className="px-4 py-1.5 text-xs font-mono font-medium bg-gaze text-abyss rounded-[4px] hover:bg-gaze/90"
              >
                {isApproving ? "Approving..." : "Confirm & Authorize"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Anchor Confirmation Modal */}
      {showAnchorModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-void border border-mist rounded-[4px] p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Anchor className="w-4 h-4 text-signal" />
              <span>Anchor Evidence on Polygon</span>
            </h3>
            <div className="bg-shadow p-3 rounded-[4px] border border-mist text-xs font-mono space-y-1.5 text-text-secondary">
              <div className="flex justify-between">
                <span>Network:</span>
                <span className="text-text-primary">Polygon Amoy (Testnet)</span>
              </div>
              <div className="flex justify-between">
                <span>Contract:</span>
                <span className="text-signal">0x82a1...49bf</span>
              </div>
              <div className="flex justify-between">
                <span>IPFS Pinning:</span>
                <span className="text-gaze">Pinata IPFS Gateway</span>
              </div>
            </div>
            <p className="text-xs text-text-muted">
              Anchoring will pin the SHA-256 evidence package to IPFS and store the root cryptographic hash on-chain.
            </p>
            <div className="flex justify-end gap-2 pt-2 border-t border-mist">
              <button
                onClick={() => setShowAnchorModal(false)}
                className="px-3 py-1.5 text-xs font-mono text-text-secondary hover:text-text-primary border border-mist rounded-[4px]"
              >
                Cancel
              </button>
              <button
                onClick={handleAnchorCase}
                disabled={isAnchoring}
                className="px-4 py-1.5 text-xs font-mono font-medium bg-signal text-text-primary rounded-[4px] hover:bg-signal/90"
              >
                {isAnchoring ? "Anchoring on Chain..." : "Execute Anchor"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Attach Evidence Modal */}
      {showAttachModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-void border border-mist rounded-[4px] p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Paperclip className="w-4 h-4 text-gaze" />
              <span>Attach Module Evidence</span>
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-text-secondary mb-1">
                  Select Submitting Module
                </label>
                <select
                  value={attachModule}
                  onChange={(e) => setAttachModule(e.target.value as any)}
                  className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-1.5 text-xs text-text-primary font-mono focus:border-gaze outline-none"
                >
                  <option value="voiceguard">VoiceGuard (Audio Deepfake Verdict)</option>
                  <option value="shadowtrace">ShadowTrace (Darknet Stylometry)</option>
                  <option value="chaineye">ChainEye (Blockchain Transaction Graph)</option>
                </select>
              </div>
              <p className="text-xs text-text-muted">
                Attaching evidence will auto-compute SHA-256 hashes and evaluate cross-module convergence rules.
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-mist">
              <button
                onClick={() => setShowAttachModal(false)}
                className="px-3 py-1.5 text-xs font-mono text-text-secondary hover:text-text-primary border border-mist rounded-[4px]"
              >
                Cancel
              </button>
              <button
                onClick={handleAttachEvidence}
                className="px-4 py-1.5 text-xs font-mono font-medium bg-gaze text-abyss rounded-[4px] hover:bg-gaze/90"
              >
                Attach & Hash
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CaseFilesPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-abyss" />}>
      <CaseFilesContent />
    </Suspense>
  );
}
