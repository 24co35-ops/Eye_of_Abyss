"use client";

import { useState } from "react";
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
} from "lucide-react";

const CASE_ID = "EOA-2026-0035";

// ── Evidence card data — Prompt 5 exact spec ──────────────────────────────
const EVIDENCE_CARDS = [
  {
    module: "VoiceGuard",
    icon: Mic,
    borderColor: "#2A9D4E",
    verdict: { label: "SYNTHETIC DETECTED", color: "#C92A2A", bg: "#C92A2A1A" },
    confidence: 91.4,
    confColor: "#C92A2A",
    finding: "AI-generated voice (TTS) confirmed in 3 call segments",
    evidenceId: "EV-VG-2026-0891",
    anchorStatus: "Pending",
    artifacts: 2,
    artifactLabels: ["waveform", "spectrogram"],
  },
  {
    module: "ShadowTrace",
    icon: Fingerprint,
    borderColor: "#6B4FFF",
    verdict: { label: "d4rk_exch4nger", color: "#F0A500", bg: "transparent" },
    confidence: 87,
    confColor: "#6B4FFF",
    finding: "Cross-platform identity confirmed — AlphaBay ↔ Telegram",
    evidenceId: "EV-ST-2026-0445",
    anchorStatus: "Pending",
    artifacts: 3,
    artifactLabels: ["fingerprint", "graph", "report"],
  },
  {
    module: "ChainEye",
    icon: Network,
    borderColor: "#F0A500",
    verdict: { label: "Binance Global", color: "#E8E6F2", bg: "transparent" },
    confidence: 82,
    confColor: "#6B4FFF",
    finding: "4.73 BTC traced across 12 wallets. Withdrawal window: Sep 16",
    evidenceId: "EV-CE-2026-0312",
    anchorStatus: "Pending",
    artifacts: 2,
    artifactLabels: ["graph", "transaction log"],
  },
];

const CONVERGENCE_SIGNALS = [
  {
    title: "Timezone Alignment",
    body: "ShadowTrace temporal profile (IST/UTC+5:30) matches ChainEye withdrawal hour distribution (peak 02:00–04:00 IST). Overlap confidence: 79%.",
  },
  {
    title: "Operational Period Overlap",
    body: "Both ShadowTrace actor profile and ChainEye wallet activity show active periods Jul–Aug 2026. 100% period overlap.",
  },
  {
    title: "Actor Graph Link",
    body: "ChainEye wallet `1BvBMSE...` appears in ShadowTrace actor network graph as a referenced transaction counterpart. Direct graph edge confirmed.",
  },
];

function ConfBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 bg-[#2A2640] rounded-full">
        <div className="h-1.5 rounded-full" style={{ width: `${value}%`, backgroundColor: color }} />
      </div>
      <span className="font-mono text-[10px] text-[#8884A8] w-10 text-right">{value}%</span>
    </div>
  );
}

export default function CaseFilePage() {
  const [anchoring, setAnchoring] = useState(false);
  const [anchored, setAnchored] = useState(false);
  const [contextOpen, setContextOpen] = useState(true);

  const handleAnchor = () => {
    if (anchored) return;
    setAnchoring(true);
    setTimeout(() => { setAnchoring(false); setAnchored(true); }, 1800);
  };

  return (
    <div className="flex h-screen bg-[#0D0B14] text-[#E8E6F2] overflow-hidden">
      <NavRail activeItem="cases" />

      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar
          onToggleContext={() => setContextOpen((o) => !o)}
          isContextOpen={contextOpen}
          activeCaseId={CASE_ID}
        />

        {/* Sub-header: case ID + status + action buttons */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#2A2640] bg-[#0D0B14]">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm font-semibold">{CASE_ID}</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#6B4FFF]/20 border border-[#6B4FFF]/40 text-[#6B4FFF]">
              CONVERGENCE_COMPUTED
            </span>
          </div>
          <div className="flex gap-2">
            <button
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-[#2A2640] text-[#8884A8] rounded hover:border-[#8884A8] transition-colors"
            >
              <Download size={12} /> Export PDF
            </button>
            <button
              onClick={handleAnchor}
              disabled={anchoring || anchored}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                anchored
                  ? "bg-[#2A9D4E]/20 border border-[#2A9D4E] text-[#2A9D4E]"
                  : anchoring
                  ? "bg-[#6B4FFF]/50 text-[#E8E6F2] cursor-wait"
                  : "bg-[#6B4FFF] text-white hover:bg-[#6B4FFF]/90"
              }`}
            >
              <Anchor size={12} />
              {anchored ? "Evidence Anchored" : anchoring ? "Anchoring…" : "Anchor Evidence"}
            </button>
          </div>
        </div>

        {/* Main + right panel */}
        <div className="flex flex-1 overflow-hidden">

          {/* ── Main content ─────────────────────────────────────── */}
          <main className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">

            {/* Case Header Card */}
            <div className="bg-[#13111E] border border-[#2A2640] rounded p-4 flex items-start justify-between gap-4">
              {/* Left: case metadata */}
              <div className="flex flex-col gap-1">
                <span className="font-mono text-lg font-medium">{CASE_ID}</span>
                <span className="text-xs text-[#8884A8]">Complainant: Redacted (Corporate Entity)</span>
                <span className="text-xs text-[#8884A8]">Reported loss: <span className="text-[#E8E6F2] font-medium">₹47.3 Lakhs</span></span>
                <span className="text-xs text-[#8884A8]">Filed: 2026-08-22</span>
              </div>

              {/* Center: convergence score */}
              <div className="flex flex-col items-center gap-1">
                <span className="text-[10px] text-[#4A4768] uppercase tracking-wider">Convergence Confidence</span>
                <span className="font-semibold text-3xl text-[#F0A500]">81%</span>
                <div className="w-32 h-1.5 bg-[#2A2640] rounded-full">
                  <div className="h-1.5 bg-[#F0A500] rounded-full" style={{ width: "81%" }} />
                </div>
              </div>

              {/* Right: module status chips */}
              <div className="flex flex-col gap-1.5">
                {["VoiceGuard", "ShadowTrace", "ChainEye"].map((m) => (
                  <div key={m} className="flex items-center gap-1.5 px-2.5 py-1 bg-[#2A9D4E]/10 border border-[#2A9D4E]/30 rounded-sm">
                    <CheckCircle2 size={11} className="text-[#2A9D4E]" />
                    <span className="text-xs font-medium text-[#2A9D4E]">{m}</span>
                    <span className="text-[10px] text-[#4A4768]">Evidence Submitted</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Three evidence cards */}
            <div className="grid grid-cols-3 gap-4">
              {EVIDENCE_CARDS.map((card) => {
                const Icon = card.icon;
                return (
                  <div
                    key={card.module}
                    className="bg-[#13111E] border border-[#2A2640] rounded p-4 flex flex-col gap-2"
                    style={{ borderLeftWidth: "4px", borderLeftColor: card.borderColor }}
                  >
                    {/* Header */}
                    <div className="flex items-center gap-2">
                      <Icon size={14} style={{ color: card.borderColor }} />
                      <span className="text-sm font-medium">{card.module}</span>
                    </div>

                    {/* Verdict */}
                    <span
                      className="text-xs font-semibold px-2 py-0.5 rounded-sm w-fit"
                      style={{ color: card.verdict.color, backgroundColor: card.verdict.bg }}
                    >
                      {card.verdict.label}
                    </span>

                    {/* Confidence bar */}
                    <div>
                      <span className="text-[10px] text-[#4A4768]">Confidence</span>
                      <ConfBar value={card.confidence} color={card.confColor} />
                    </div>

                    {/* Finding */}
                    <p className="text-[11px] text-[#8884A8] leading-relaxed">{card.finding}</p>

                    {/* Evidence ID */}
                    <div className="flex items-center justify-between border-t border-[#2A2640] pt-2 mt-1">
                      <span className="font-mono text-[10px] text-[#4A4768]">{card.evidenceId}</span>
                      <span className="text-[10px] text-[#4A4768]">Anchor: {anchored ? "✓" : card.anchorStatus}</span>
                    </div>

                    {/* Artifacts */}
                    <div className="flex items-center gap-1.5 text-[10px] text-[#4A4768]">
                      <Paperclip size={10} />
                      <span>{card.artifacts} artifacts:</span>
                      {card.artifactLabels.map((a) => (
                        <span key={a} className="px-1.5 py-0.5 bg-[#1C1929] border border-[#2A2640] rounded-sm">{a}</span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Convergence Report */}
            <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
              <h2 className="text-sm font-semibold mb-4">Cross-Module Convergence Report</h2>

              <div className="flex flex-col gap-3">
                {CONVERGENCE_SIGNALS.map((sig, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="w-1 shrink-0 bg-[#6B4FFF] rounded-full mt-0.5" />
                    <div>
                      <p className="text-xs font-medium text-[#E8E6F2] mb-0.5">{sig.title}</p>
                      <p className="text-xs text-[#8884A8] leading-relaxed">{sig.body}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Composite score */}
              <div className="mt-6 pt-4 border-t border-[#2A2640]">
                <div className="flex items-baseline gap-3 mb-1">
                  <span className="text-[10px] text-[#4A4768] uppercase tracking-wider">Composite Convergence Confidence</span>
                  <span className="text-2xl font-semibold text-[#F0A500]">81%</span>
                </div>
                <p className="text-xs text-[#8884A8] mb-4">
                  Three independent investigation tracks converge on a single actor.
                </p>

                {/* Anchor All Evidence — full width, indigo filled */}
                <button
                  onClick={handleAnchor}
                  disabled={anchoring || anchored}
                  className={`w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded transition-all ${
                    anchored
                      ? "bg-[#2A9D4E]/20 border border-[#2A9D4E] text-[#2A9D4E]"
                      : anchoring
                      ? "bg-[#6B4FFF]/50 text-[#E8E6F2] cursor-wait"
                      : "bg-[#6B4FFF] text-white hover:bg-[#6B4FFF]/90"
                  }`}
                >
                  <Anchor size={14} />
                  {anchored ? "All Evidence Anchored on Polygon" : anchoring ? "Writing to blockchain…" : "Anchor All Evidence"}
                </button>
              </div>
            </div>

          </main>

          {/* ── Right context panel: Blockchain Record ────────────── */}
          {contextOpen && (
            <aside className="w-[320px] min-w-[320px] border-l border-[#2A2640] bg-[#13111E] flex flex-col overflow-y-auto">
              <div className="px-4 py-3 border-b border-[#2A2640] bg-[#1C1929] flex items-center gap-2">
                <ShieldCheck size={14} className="text-[#F0A500]" />
                <span className="text-xs font-semibold uppercase tracking-wider text-[#E8E6F2]">Blockchain Record</span>
              </div>

              <div className="flex-1 p-4 flex flex-col gap-4">
                {/* Network status */}
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full bg-[#2A9D4E] animate-pulse" />
                  <span className="text-[#2A9D4E] font-mono">Polygon Mumbai Testnet: Connected</span>
                </div>

                {/* Anchor state */}
                {!anchored ? (
                  <div className="flex flex-col items-center gap-3 py-8 text-center">
                    <div className="w-12 h-12 rounded-full border border-[#2A2640] flex items-center justify-center">
                      <Circle size={24} className="text-[#4A4768]" />
                    </div>
                    <p className="text-xs text-[#4A4768]">No anchors recorded</p>
                    <p className="text-[11px] text-[#4A4768] leading-relaxed max-w-[200px]">
                      Submit evidence for anchoring to create a tamper-proof record.
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-3">
                    <p className="text-[10px] text-[#4A4768] uppercase tracking-wider">Anchor Events</p>
                    {EVIDENCE_CARDS.map((card, i) => (
                      <div key={card.module} className="bg-[#1C1929] border border-[#2A2640] rounded p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle2 size={12} className="text-[#2A9D4E]" />
                          <span className="text-xs font-medium">{card.module}</span>
                          <span className="ml-auto text-[10px] text-[#4A4768]">just now</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-[#4A4768]">
                          <Link2 size={9} />
                          <span className="font-mono">
                            0x{Math.random().toString(16).slice(2, 6)}…{Math.random().toString(16).slice(2, 6)}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 mt-1">
                          <span className="font-mono text-[10px] text-[#4A4768]">Block #49{20190 + i * 13}</span>
                          <span className="ml-auto px-1.5 py-0.5 bg-[#2A9D4E]/10 border border-[#2A9D4E]/30 text-[#2A9D4E] text-[9px] rounded-sm">Verified</span>
                        </div>
                      </div>
                    ))}
                    <div className="mt-2 text-[10px] text-[#4A4768] font-mono text-center">
                      IPFS: {CASE_ID.toLowerCase().replace(/-/g, "")} · Polygon
                    </div>
                  </div>
                )}

                {/* Case summary */}
                <div className="border-t border-[#2A2640] pt-3 mt-auto">
                  <p className="text-[10px] text-[#4A4768] uppercase tracking-wider mb-2">Case Summary</p>
                  {[
                    ["Complainant", "Redacted (Corporate)"],
                    ["Reported loss", "₹47.3 Lakhs"],
                    ["Filed", "2026-08-22"],
                    ["Modules", "VG · ST · CE"],
                    ["Status", "CONVERGENCE_COMPUTED"],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[11px] py-0.5 border-b border-[#2A2640]/40">
                      <span className="text-[#4A4768]">{k}</span>
                      <span className="font-mono text-[#8884A8]">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          )}

        </div>
      </div>
    </div>
  );
}
