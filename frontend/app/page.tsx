"use client";

import React, { useEffect, useState } from "react";
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
} from "lucide-react";
import { api, MOCK_CASES, MOCK_ANCHORS, MOCK_MODULE_STATUSES } from "@/lib/api";
import { CaseRecord, AnchorEvent, ModuleStatusRecord } from "@/lib/types";

export default function CommandCenter() {
  const [activeNav, setActiveNav] = useState<NavItem>("dashboard");
  const [cases, setCases] = useState<CaseRecord[]>(MOCK_CASES);
  const [anchors, setAnchors] = useState<AnchorEvent[]>(MOCK_ANCHORS);
  const [moduleStatuses, setModuleStatuses] = useState<ModuleStatusRecord[]>(MOCK_MODULE_STATUSES);
  
  // Prompt 1: Initial selected case is EOA-2026-0041 (first row highlighted with amber border)
  const [selectedCase, setSelectedCase] = useState<CaseRecord | null>(MOCK_CASES[0]);
  const [isContextOpen, setIsContextOpen] = useState(false); // Collapsed initially per Prompt 1

  // Load from Case Engine API with mock fallback
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const [caseList, anchorList, moduleList] = await Promise.all([
          api.cases.list(),
          api.anchors.recent(),
          api.modules.statuses(),
        ]);
        if (isMounted) {
          if (caseList && caseList.length > 0) setCases(caseList);
          if (anchorList && anchorList.length > 0) setAnchors(anchorList);
          if (moduleList && moduleList.length > 0) setModuleStatuses(moduleList);
        }
      } catch {
        // Fallback to mock data already initialized
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleRowClick = (caseItem: CaseRecord) => {
    setSelectedCase(caseItem);
    setIsContextOpen(true);
  };

  return (
    <div className="flex h-screen w-screen bg-abyss text-text-primary overflow-hidden font-sans select-none">
      {/* Left navigation rail: 56px wide (icon-only), Dashboard active in #F0A500 */}
      <NavRail activeItem={activeNav} onSelect={setActiveNav} />

      {/* Main Container */}
      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
        {/* Top bar: 48px height */}
        <TopBar
          isContextOpen={isContextOpen}
          onToggleContext={() => setIsContextOpen(!isContextOpen)}
          activeCaseId={selectedCase?.caseId}
        />

        {/* Content Area + Sliding Right Context Panel */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Content: Left-aligned, 8px grid, high data density */}
          <main className="flex-1 overflow-y-auto p-4 space-y-4">
            
            {/* ROW 1: Stat bar (4 cards, horizontal) */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Card 1: Active Cases (Amber) */}
              <div className="bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between hover:border-gaze/50 transition-colors">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">Active Cases</span>
                  <span className="text-gaze text-[11px] font-mono font-medium flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" /> +3 this week
                  </span>
                </div>
                <div className="text-[40px] font-mono font-semibold text-gaze mt-1.5 leading-none">
                  23
                </div>
                <div className="text-[10px] text-text-muted mt-2 font-mono">
                  8 PRIORITY INVESTIGATIONS
                </div>
              </div>

              {/* Card 2: Evidence Anchored Today (Indigo) */}
              <div className="bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between hover:border-signal/50 transition-colors">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">Evidence Anchored Today</span>
                  <span className="text-signal text-[11px] font-mono font-medium flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> Polygon confirmed
                  </span>
                </div>
                <div className="text-[40px] font-mono font-semibold text-signal mt-1.5 leading-none">
                  7
                </div>
                <div className="text-[10px] text-text-muted mt-2 font-mono">
                  BLOCKCHAIN REGISTRY SYNCED
                </div>
              </div>

              {/* Card 3: Synthetic Voice Alerts (Crimson) */}
              <div className="bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between hover:border-threat/50 transition-colors">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">Synthetic Voice Alerts</span>
                  <span className="text-threat text-[11px] font-mono font-medium flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Last 24h
                  </span>
                </div>
                <div className="text-[40px] font-mono font-semibold text-threat mt-1.5 leading-none">
                  2
                </div>
                <div className="text-[10px] text-text-muted mt-2 font-mono">
                  ECAPA-TDNN HIGH CONFIDENCE
                </div>
              </div>

              {/* Card 4: Predicted Withdrawal Alerts (Crimson, Pulsing Border) */}
              <div className="bg-void border border-threat/60 rounded-[4px] p-3 flex flex-col justify-between animate-pulse">
                <div className="flex items-center justify-between text-text-secondary text-xs">
                  <span className="font-medium text-text-secondary">Predicted Withdrawal Alerts</span>
                  <span className="text-threat text-[11px] font-mono font-bold">
                    Action required
                  </span>
                </div>
                <div className="text-[40px] font-mono font-semibold text-threat mt-1.5 leading-none">
                  1
                </div>
                <div className="text-[10px] text-threat font-mono font-medium mt-2">
                  EST. WINDOW: &lt; 4.2 HOURS
                </div>
              </div>
            </section>

            {/* ROW 2: Active Cases Table */}
            <section className="bg-void border border-mist rounded-[4px] overflow-hidden">
              {/* Header: "Active Cases" in Space Grotesk 600 16px + "New Case" button */}
              <div className="px-3.5 py-2.5 border-b border-mist flex items-center justify-between bg-shadow/60">
                <h2 className="text-[16px] font-semibold text-text-primary tracking-tight">
                  Active Cases
                </h2>

                <button className="px-3 py-1 bg-transparent hover:bg-gaze hover:text-abyss text-gaze border border-gaze rounded-[4px] text-xs font-mono font-medium transition-colors flex items-center gap-1.5">
                  <Plus className="w-3.5 h-3.5" />
                  <span>New Case</span>
                </button>
              </div>

              {/* Table with the 5 exact rows */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-mist bg-shadow/30 text-text-muted font-mono uppercase text-[10px] tracking-wider">
                      <th className="py-2.5 px-3.5 font-medium">Case ID</th>
                      <th className="py-2.5 px-3 font-medium">Complainant Type</th>
                      <th className="py-2.5 px-3 font-medium">Modules Active</th>
                      <th className="py-2.5 px-3 font-medium">Status</th>
                      <th className="py-2.5 px-3 font-medium">Threat Tier</th>
                      <th className="py-2.5 px-3.5 text-right font-medium">Last Updated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-mist/50 font-sans">
                    {cases.map((c) => {
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
                          {/* Case ID in JetBrains Mono */}
                          <td className="py-2.5 px-3.5 font-mono font-medium text-gaze whitespace-nowrap">
                            {c.caseId}
                          </td>

                          {/* Complainant Type */}
                          <td className="py-2.5 px-3 text-text-primary font-medium">
                            {c.complainant}
                          </td>

                          {/* Modules Active (small icon chips — VG/ST/CE) */}
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
                                  title={`${mod} active`}
                                >
                                  {mod}
                                </span>
                              ))}
                            </div>
                          </td>

                          {/* Status Badge (Pill shape only exception) */}
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

                          {/* Threat Tier */}
                          <td className="py-2.5 px-3 font-mono text-[11px] text-text-secondary">
                            {c.threatTier}
                          </td>

                          {/* Last Updated */}
                          <td className="py-2.5 px-3.5 text-right font-mono text-text-muted text-[11px] whitespace-nowrap">
                            {c.lastUpdated}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>

            {/* ROW 3: Two panels side by side */}
            <section className="grid grid-cols-1 lg:grid-cols-12 gap-3">
              
              {/* Left Panel (60% width): "Recent Evidence Anchors" */}
              <div className="lg:col-span-7 bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-mist pb-2 mb-2.5">
                    <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider font-mono">
                      Recent Evidence Anchors
                    </h3>
                    <span className="text-[10px] font-mono text-text-muted">
                      POLYGON AMOY // TESTNET
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
                            {/* Amber diamond icon */}
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
                            {/* Tx Hash in JetBrains Mono truncated */}
                            <span className="font-mono text-[11px] text-signal hover:underline cursor-pointer">
                              {truncatedTx}
                            </span>

                            {/* Timestamp */}
                            <span className="font-mono text-[11px] text-text-muted">
                              {anc.timestamp}
                            </span>

                            {/* Green "Verified" Label */}
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
                  <span className="text-gaze">LATEST ANCHOR: 2 MIN AGO</span>
                </div>
              </div>

              {/* Right Panel (40% width): "Module Status" */}
              <div className="lg:col-span-5 bg-void border border-mist rounded-[4px] p-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-mist pb-2 mb-2.5">
                    <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider font-mono">
                      Module Status
                    </h3>
                    <span className="text-[10px] font-mono text-safe flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-safe animate-ping" />
                      3/3 ENGINES ONLINE
                    </span>
                  </div>

                  {/* Three module status indicators stacked */}
                  <div className="space-y-2">
                    {moduleStatuses.map((mod) => (
                      <div
                        key={mod.name}
                        className="bg-shadow/50 border border-mist rounded-[4px] p-2.5 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2.5">
                          {/* Module Icon */}
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

                        {/* Status Dot + Text */}
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              mod.statusColor === "green"
                                ? "bg-safe"
                                : mod.statusColor === "amber"
                                ? "bg-gaze animate-pulse"
                                : "bg-threat"
                            }`}
                          />
                          <span
                            className={`text-xs font-mono font-medium ${
                              mod.statusColor === "green"
                                ? "text-safe"
                                : mod.statusColor === "amber"
                                ? "text-gaze"
                                : "text-threat"
                            }`}
                          >
                            {mod.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-2 text-[10px] font-mono text-text-muted border-t border-mist/50 mt-2 flex items-center justify-between">
                  <span>TELEMETRY SYNC: ACTIVE</span>
                  <span className="text-signal">WS: CONNECTED</span>
                </div>
              </div>

            </section>

          </main>

          {/* Right context panel: 320px (slides in when case selected) */}
          <ContextPanel
            isOpen={isContextOpen}
            onClose={() => setIsContextOpen(false)}
            caseData={selectedCase}
          />
        </div>
      </div>
    </div>
  );
}
