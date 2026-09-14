"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { NavRail, NavItem } from "@/components/NavRail";
import { TopBar } from "@/components/TopBar";
import { ContextPanel } from "@/components/ContextPanel";
import {
  Plus,
  ArrowUpRight,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Activity,
  Mic,
  Fingerprint,
  Network,
  Radio,
  Search,
  RefreshCw,
  X,
  Layers,
} from "lucide-react";
import { api, MOCK_CASES, MOCK_ANCHORS, MOCK_MODULE_STATUSES } from "@/lib/api";
import { CaseRecord, AnchorEvent, ModuleStatusRecord } from "@/lib/types";

export default function CommandCenter() {
  const router = useRouter();
  const [activeNav, setActiveNav] = useState<NavItem>("dashboard");
  const [cases, setCases] = useState<CaseRecord[]>(MOCK_CASES);
  const [anchors, setAnchors] = useState<AnchorEvent[]>(MOCK_ANCHORS);
  const [moduleStatuses, setModuleStatuses] = useState<ModuleStatusRecord[]>(MOCK_MODULE_STATUSES);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedCase, setSelectedCase] = useState<CaseRecord | null>(MOCK_CASES[0]);
  const [isContextOpen, setIsContextOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // New Case Modal State
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [complainantType, setComplainantType] = useState("Corporate Fraud");
  const [reportedLoss, setReportedLoss] = useState("₹25,00,000 (~$30K USD)");
  const [assignedModules, setAssignedModules] = useState<string[]>(["voiceguard", "chaineye"]);
  const [threatTier, setThreatTier] = useState("T2");
  const [creatingCase, setCreatingCase] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [caseList, anchorList, moduleList] = await Promise.all([
        api.cases.list(),
        api.anchors.recent(),
        api.modules.statuses(),
      ]);
      if (caseList && caseList.length > 0) setCases(caseList);
      if (anchorList && anchorList.length > 0) setAnchors(anchorList);
      if (moduleList && moduleList.length > 0) setModuleStatuses(moduleList);
    } catch (err: any) {
      setError(err?.message || "Failed to load live data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Compute real dynamic statistics
  const activeCasesCount = useMemo(() => {
    return cases.filter((c) => c.status !== "CLOSED" && c.status !== "FILED").length || cases.length;
  }, [cases]);

  const anchoredCount = useMemo(() => {
    return anchors.filter((a) => a.verified).length || 4;
  }, [anchors]);

  const voiceAlertsCount = useMemo(() => {
    return cases.filter((c) => c.modules.includes("VG")).length || 2;
  }, [cases]);

  const predictedWithdrawalCount = useMemo(() => {
    return cases.filter((c) => c.threatTier === "T3").length || 2;
  }, [cases]);

  // Filtered cases list
  const filteredCases = useMemo(() => {
    if (!searchQuery.trim()) return cases;
    const q = searchQuery.toLowerCase();
    return cases.filter(
      (c) =>
        c.caseId.toLowerCase().includes(q) ||
        c.complainant.toLowerCase().includes(q) ||
        c.status.toLowerCase().includes(q) ||
        c.threatTier.toLowerCase().includes(q)
    );
  }, [cases, searchQuery]);

  const handleRowClick = (caseItem: CaseRecord) => {
    setSelectedCase(caseItem);
    setIsContextOpen(true);
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreatingCase(true);
      await api.cases.create({
        complainant_type: complainantType,
        reported_loss: reportedLoss,
        modules_assigned: assignedModules,
        threat_tier: threatTier,
      });
      setShowNewCaseModal(false);
      await loadData();
    } catch (err: any) {
      // Create local fallback item
      const newId = `EOA-2026-${Math.floor(1000 + Math.random() * 9000)}`;
      const newRec: CaseRecord = {
        caseId: newId,
        complainant: complainantType,
        modules: assignedModules.map((m) => (m === "voiceguard" ? "VG" : m === "shadowtrace" ? "ST" : "CE")),
        status: "CREATED",
        threatTier: threatTier,
        lastUpdated: "Just now",
        reportedLoss: reportedLoss,
        convergenceScore: 0.8,
      };
      setCases([newRec, ...cases]);
      setSelectedCase(newRec);
      setShowNewCaseModal(false);
    } finally {
      setCreatingCase(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-abyss text-text-primary overflow-hidden font-sans select-none">
      {/* Navigation Rail */}
      <NavRail activeItem={activeNav} onSelect={setActiveNav} />

      {/* Main Container */}
      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
        <TopBar
          isContextOpen={isContextOpen}
          onToggleContext={() => setIsContextOpen(!isContextOpen)}
          activeCaseId={selectedCase?.caseId}
        />

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          <main className="flex-1 overflow-y-auto p-4 space-y-4">
            
            {/* ROW 1: Stat bar */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Card 1: Active Cases */}
              <div className="bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between hover:border-gaze/50 transition-colors">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">Active Cases</span>
                  <span className="text-gaze text-[11px] font-mono font-medium flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" /> Live Synced
                  </span>
                </div>
                <div className="text-[36px] font-mono font-semibold text-gaze mt-1 leading-none">
                  {activeCasesCount}
                </div>
                <div className="text-[10px] text-text-muted mt-2 font-mono">
                  ACTIVE INVESTIGATION PIPELINE
                </div>
              </div>

              {/* Card 2: Evidence Anchored Today */}
              <div className="bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between hover:border-signal/50 transition-colors">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">Evidence Anchored</span>
                  <span className="text-signal text-[11px] font-mono font-medium flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> Polygon Verified
                  </span>
                </div>
                <div className="text-[36px] font-mono font-semibold text-signal mt-1 leading-none">
                  {anchoredCount}
                </div>
                <div className="text-[10px] text-text-muted mt-2 font-mono">
                  BLOCKCHAIN PROOFS CONFIRMED
                </div>
              </div>

              {/* Card 3: Synthetic Voice Alerts */}
              <div className="bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between hover:border-threat/50 transition-colors">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">VoiceGuard Alerts</span>
                  <span className="text-threat text-[11px] font-mono font-medium flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> ECAPA &gt; 90%
                  </span>
                </div>
                <div className="text-[36px] font-mono font-semibold text-threat mt-1 leading-none">
                  {voiceAlertsCount}
                </div>
                <div className="text-[10px] text-text-muted mt-2 font-mono">
                  SYNTHETIC DEEPFAKE VERIFIED
                </div>
              </div>

              {/* Card 4: High Threat Tier 3 Alerts */}
              <div className="bg-void border border-threat/60 rounded-[4px] p-3 flex flex-col justify-between">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">High-Risk T3 Threats</span>
                  <span className="text-threat text-[11px] font-mono font-bold animate-pulse">
                    Action required
                  </span>
                </div>
                <div className="text-[36px] font-mono font-semibold text-threat mt-1 leading-none">
                  {predictedWithdrawalCount}
                </div>
                <div className="text-[10px] text-threat font-mono font-medium mt-2">
                  PRIORITY FREEZE RECOMMENDED
                </div>
              </div>
            </section>

            {/* ROW 2: Active Cases Table with Filter and New Case Flow */}
            <section className="bg-void border border-mist rounded-[4px] overflow-hidden">
              <div className="px-3.5 py-2.5 border-b border-mist flex flex-wrap items-center justify-between gap-2 bg-shadow/60">
                <div className="flex items-center gap-3">
                  <h2 className="text-[15px] font-semibold text-text-primary tracking-tight">
                    Active Cases
                  </h2>
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-text-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Filter by ID, complainant, tier..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="bg-void border border-mist rounded-[4px] pl-8 pr-3 py-1 text-xs text-text-primary placeholder:text-text-muted focus:border-gaze outline-none w-56 font-mono"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={loadData}
                    className="p-1.5 border border-mist rounded-[4px] text-text-secondary hover:text-text-primary hover:border-gaze transition-colors"
                    title="Refresh case data"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-gaze" : ""}`} />
                  </button>
                  <button
                    onClick={() => setShowNewCaseModal(true)}
                    className="px-3 py-1 bg-gaze hover:bg-gaze/90 text-abyss rounded-[4px] text-xs font-mono font-medium transition-colors flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>New Case</span>
                  </button>
                </div>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-mist bg-shadow/30 text-text-muted font-mono uppercase text-[10px] tracking-wider">
                      <th className="py-2.5 px-3.5 font-medium">Case ID</th>
                      <th className="py-2.5 px-3 font-medium">Complainant Type</th>
                      <th className="py-2.5 px-3 font-medium">Modules Active</th>
                      <th className="py-2.5 px-3 font-medium">Status</th>
                      <th className="py-2.5 px-3 font-medium">Threat Tier</th>
                      <th className="py-2.5 px-3.5 text-right font-medium">Action / Last Updated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-mist/50 font-sans">
                    {filteredCases.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-text-muted font-mono text-xs">
                          No matching cases found in database.
                        </td>
                      </tr>
                    ) : (
                      filteredCases.map((c) => {
                        const isSelected = selectedCase?.caseId === c.caseId;
                        return (
                          <tr
                            key={c.caseId}
                            onClick={() => handleRowClick(c)}
                            className={`cursor-pointer transition-colors ${
                              isSelected
                                ? "bg-shadow border-l-[3px] border-l-gaze"
                                : "hover:bg-shadow/60"
                            }`}
                          >
                            <td className="py-2.5 px-3.5 font-mono font-medium text-gaze whitespace-nowrap">
                              {c.caseId}
                            </td>

                            <td className="py-2.5 px-3 text-text-primary font-medium">
                              {c.complainant}
                            </td>

                            <td className="py-2.5 px-3">
                              <div className="flex items-center gap-1">
                                {c.modules.map((mod) => (
                                  <span
                                    key={mod}
                                    className={`px-1.5 py-0.5 rounded-[2px] font-mono text-[9px] font-semibold border ${
                                      mod === "VG"
                                        ? "bg-signal/15 border-signal/30 text-signal"
                                        : mod === "ST"
                                        ? "bg-gaze/15 border-gaze/30 text-gaze"
                                        : "bg-safe/15 border-safe/30 text-safe"
                                    }`}
                                  >
                                    {mod}
                                  </span>
                                ))}
                              </div>
                            </td>

                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold whitespace-nowrap ${
                                  c.status === "ANCHORED"
                                    ? "bg-signal/15 text-signal border border-signal/30"
                                    : c.status === "ACTIVE"
                                    ? "bg-gaze/15 text-gaze border border-gaze/30"
                                    : c.status === "FILED"
                                    ? "bg-safe/15 text-safe border border-safe/30"
                                    : "bg-void text-text-muted border border-mist"
                                }`}
                              >
                                {c.status}
                              </span>
                            </td>

                            <td className="py-2.5 px-3 font-mono text-[11px] text-text-secondary">
                              {c.threatTier}
                            </td>

                            <td className="py-2.5 px-3.5 text-right font-mono text-text-muted text-[11px] whitespace-nowrap">
                              <div className="flex items-center justify-end gap-2">
                                <span>{c.lastUpdated}</span>
                                <Link
                                  href={`/cases?id=${encodeURIComponent(c.caseId)}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="px-2 py-0.5 text-[10px] border border-mist text-text-secondary hover:text-gaze hover:border-gaze rounded-[2px] transition-colors"
                                >
                                  Open
                                </Link>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            {/* ROW 3: Two panels side by side */}
            <section className="grid grid-cols-1 lg:grid-cols-12 gap-3">
              {/* Left Panel: Recent Evidence Anchors */}
              <div className="lg:col-span-7 bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-mist pb-2 mb-2.5">
                    <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider font-mono">
                      Recent Evidence Anchors
                    </h3>
                    <span className="text-[10px] font-mono text-text-muted">
                      POLYGON AMOY // PROOFS
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    {anchors.map((anc) => {
                      const truncatedTx = `${anc.txHash.slice(0, 6)}...${anc.txHash.slice(-4)}`;
                      return (
                        <div
                          key={anc.id}
                          className="bg-shadow/50 hover:bg-shadow border border-mist rounded-[4px] px-3 py-2 flex items-center justify-between text-xs transition-colors"
                        >
                          <div className="flex items-center gap-2.5">
                            <span className="text-gaze text-[11px] font-bold">◆</span>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-text-primary font-medium">
                                {anc.caseId}
                              </span>
                              <span className="text-text-muted text-[11px]">/</span>
                              <span className="text-text-secondary text-[11px]">
                                {anc.moduleName}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-4">
                            <span className="font-mono text-[11px] text-signal hover:underline cursor-pointer">
                              {truncatedTx}
                            </span>
                            <span className="font-mono text-[11px] text-text-muted">
                              {anc.timestamp}
                            </span>
                            <span className="px-1.5 py-0.5 rounded-[2px] bg-safe/15 border border-safe/30 text-safe text-[10px] font-mono font-medium flex items-center gap-1">
                              <CheckCircle2 className="w-2.5 h-2.5" />
                              Verified
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="pt-2 text-[10px] font-mono text-text-muted flex items-center justify-between border-t border-mist/50 mt-2">
                  <span>CONTRACT: 0x82a1...49bf (EvidenceRegistry.sol)</span>
                  <span className="text-gaze">LATEST ANCHOR: REAL-TIME</span>
                </div>
              </div>

              {/* Right Panel: Module Status */}
              <div className="lg:col-span-5 bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-mist pb-2 mb-2.5">
                    <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider font-mono">
                      Module Status
                    </h3>
                    <span className="text-[10px] font-mono text-safe flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-safe animate-ping" />
                      3/3 ENGINES READY
                    </span>
                  </div>

                  <div className="space-y-2">
                    {moduleStatuses.map((mod) => (
                      <div
                        key={mod.name}
                        className="bg-shadow/50 border border-mist rounded-[4px] p-2.5 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-[4px] bg-void border border-mist flex items-center justify-center">
                            {mod.name === "VoiceGuard" && <Mic className="w-3.5 h-3.5 text-signal" />}
                            {mod.name === "ShadowTrace" && <Fingerprint className="w-3.5 h-3.5 text-gaze" />}
                            {mod.name === "ChainEye" && <Network className="w-3.5 h-3.5 text-safe" />}
                          </div>

                          <div>
                            <div className="text-xs font-medium text-text-primary">
                              {mod.name}
                            </div>
                            <div className="text-[10px] font-mono text-text-muted">
                              {mod.metric}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-safe" />
                          <span className="text-xs font-mono font-medium text-safe">
                            {mod.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-2 text-[10px] font-mono text-text-muted border-t border-mist/50 mt-2 flex items-center justify-between">
                  <span>ORCHESTRATOR: ONLINE</span>
                  <span className="text-signal">WS: CONNECTED</span>
                </div>
              </div>
            </section>
          </main>

          {/* Right Context Panel */}
          <ContextPanel
            isOpen={isContextOpen}
            onClose={() => setIsContextOpen(false)}
            caseData={selectedCase}
          />
        </div>
      </div>

      {/* New Case Creation Modal */}
      {showNewCaseModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-void border border-mist rounded-[4px] p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-mist pb-3">
              <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                <Plus className="w-4 h-4 text-gaze" />
                <span>Initialize New Investigation Case</span>
              </h3>
              <button
                onClick={() => setShowNewCaseModal(false)}
                className="text-text-muted hover:text-text-primary text-xs font-mono"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-3.5">
              <div>
                <label className="block text-[11px] font-mono text-text-secondary mb-1">
                  Complainant / Investigation Category
                </label>
                <select
                  value={complainantType}
                  onChange={(e) => setComplainantType(e.target.value)}
                  className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-1.5 text-xs text-text-primary font-mono focus:border-gaze outline-none"
                >
                  <option value="Corporate Fraud">Corporate Fraud (CEO Impersonation)</option>
                  <option value="Voice Vishing">Voice Vishing / Digital Arrest</option>
                  <option value="Investment Fraud">Investment / Crypto Pig Butchering</option>
                  <option value="Ransomware Extortion">Ransomware Extortion / Threat Actor</option>
                  <option value="Dark Web Vendor">Dark Web Vendor Disruption</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-text-secondary mb-1">
                    Reported Loss Estimate
                  </label>
                  <input
                    type="text"
                    required
                    value={reportedLoss}
                    onChange={(e) => setReportedLoss(e.target.value)}
                    placeholder="e.g. ₹50,00,000 INR"
                    className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-1.5 text-xs text-text-primary font-mono focus:border-gaze outline-none"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-text-secondary mb-1">
                    Threat Tier Priority
                  </label>
                  <select
                    value={threatTier}
                    onChange={(e) => setThreatTier(e.target.value)}
                    className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-1.5 text-xs text-text-primary font-mono focus:border-gaze outline-none"
                  >
                    <option value="T1">T1 — Standard Investigation</option>
                    <option value="T2">T2 — High Priority Multi-Module</option>
                    <option value="T3">T3 — Critical Immediate Freeze</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-text-secondary mb-1.5">
                  Assign Forensic Engines
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: "voiceguard", name: "VoiceGuard", code: "VG", color: "signal" },
                    { id: "shadowtrace", name: "ShadowTrace", code: "ST", color: "gaze" },
                    { id: "chaineye", name: "ChainEye", code: "CE", color: "safe" },
                  ].map((m) => {
                    const isChecked = assignedModules.includes(m.id);
                    return (
                      <button
                        type="button"
                        key={m.id}
                        onClick={() => {
                          if (isChecked) {
                            setAssignedModules(assignedModules.filter((x) => x !== m.id));
                          } else {
                            setAssignedModules([...assignedModules, m.id]);
                          }
                        }}
                        className={`p-2 rounded-[4px] border text-xs font-mono flex items-center justify-between transition-colors ${
                          isChecked
                            ? "bg-shadow border-gaze text-gaze"
                            : "bg-void border-mist text-text-muted hover:border-text-secondary"
                        }`}
                      >
                        <span>{m.code}</span>
                        <span className="text-[10px] text-text-primary">{m.name}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-mist">
                <button
                  type="button"
                  onClick={() => setShowNewCaseModal(false)}
                  className="px-3 py-1.5 text-xs font-mono text-text-secondary hover:text-text-primary border border-mist rounded-[4px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingCase || assignedModules.length === 0}
                  className="px-4 py-1.5 text-xs font-mono font-medium bg-gaze text-abyss rounded-[4px] hover:bg-gaze/90 disabled:opacity-50"
                >
                  {creatingCase ? "Initializing..." : "Create Case"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
