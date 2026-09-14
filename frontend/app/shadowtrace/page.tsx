"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { NavRail } from "@/components/NavRail";
import { TopBar } from "@/components/TopBar";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  Cell,
  ReferenceLine,
  Tooltip,
} from "recharts";
import { ExternalLink, PlusCircle, Send } from "lucide-react";
import { api } from "@/lib/api";

// ── compact actor network (Cytoscape, browser-only) ───────────────────────
const ActorGraph = dynamic(() => import("@/components/ActorNetworkGraph"), { ssr: false });

// ── Static data — Prompt 4 exact spec ─────────────────────────────────────
const CASE_ID = "EOA-2026-0035";

const RADAR_DATA = [
  { axis: "Vocab Richness",      value: 0.61 },
  { axis: "Syntactic Complexity",value: 0.42 },
  { axis: "Punct Density",       value: 0.20 },
  { axis: "Avg Sentence Len",    value: 0.55 },
  { axis: "Code-Switching",      value: 0.70 },
  { axis: "Typo Rate",           value: 0.80 },
];

// 24-hour posting activity — spikes at 01–04 UTC and 21–23 UTC
const HOURLY: { h: number; v: number }[] = Array.from({ length: 24 }, (_, h) => {
  let v = 2 + Math.round(Math.random() * 3);
  if (h >= 1 && h <= 4)   v = 18 + Math.round(Math.random() * 10);
  if (h >= 21 && h <= 23) v = 12 + Math.round(Math.random() * 8);
  return { h, v };
});

const MATCHES = [
  {
    rank: 1,
    handle: "d4rk_exch4nger",
    platform: "AlphaBay / Telegram",
    confidence: 87,
    signals: { lex: 91, syn: 84, temp: 79 },
    crossPlatform: "AlphaBay ↔ Telegram — confirmed",
    highlighted: true,
  },
  {
    rank: 2,
    handle: "vendorX_88",
    platform: "Hansa / IRC",
    confidence: 61,
    signals: { lex: 67, syn: 59, temp: 55 },
    crossPlatform: null,
    highlighted: false,
  },
  {
    rank: 3,
    handle: "anonymous_drop",
    platform: "Empire Market",
    confidence: 34,
    signals: { lex: 38, syn: 31, temp: 29 },
    crossPlatform: null,
    highlighted: false,
  },
];

const SAMPLE_TEXT = `lookin for buyers fr the full drop, min 50 pcs, \nverified vendors only no new accs. payment btc \nor xmr. dnt waste my time with questions check \nmy prev listings. delivery in 48h max`;

// ── Confidence bar ─────────────────────────────────────────────────────────
function ConfBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[#2A2640] rounded-full">
        <div className="h-1.5 rounded-full transition-all" style={{ width: `${value}%`, backgroundColor: color }} />
      </div>
      <span className="font-mono text-xs text-[#E8E6F2] w-8 text-right">{value}%</span>
    </div>
  );
}

export default function ShadowTracePage() {
  const [contextOpen, setContextOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [actorHandle, setActorHandle] = useState("");
  const [platform, setPlatform] = useState("Dark Web Forum");
  const [sampleText, setSampleText] = useState("");
  const [activityHour, setActivityHour] = useState("02");
  const [addSuccess, setAddSuccess] = useState(false);

  const handleAddSample = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actorHandle || !sampleText) return;
    try {
      const ST_URL = process.env.NEXT_PUBLIC_SHADOWTRACE_URL ?? "http://localhost:8003";
      await fetch(`${ST_URL}/actors/${encodeURIComponent(actorHandle)}/samples`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: sampleText,
          hour_utc: parseInt(activityHour, 10),
          platform: platform,
        }),
      }).catch(() => {});
    } catch {
      // Offline fallback
    }
    setAddSuccess(true);
    setTimeout(() => {
      setAddSuccess(false);
      setShowAddModal(false);
      setSampleText("");
      setActorHandle("");
    }, 1500);
  };

  return (
    <div className="flex h-screen bg-[#0D0B14] text-[#E8E6F2] overflow-hidden">
      <NavRail activeItem="shadowtrace" />

      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar
          onToggleContext={() => setContextOpen((o) => !o)}
          isContextOpen={contextOpen}
          activeCaseId={CASE_ID}
        />

        {/* Breadcrumb + actions */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#2A2640] bg-[#0D0B14]">
          <nav className="flex items-center gap-1.5 text-xs text-[#4A4768]">
            <span>Cases</span><span>/</span>
            <span className="font-mono text-[#8884A8]">{CASE_ID}</span>
            <span>/</span>
            <span className="text-[#E8E6F2]">ShadowTrace</span>
          </nav>
          <div className="flex gap-2">
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-[#2A2640] text-[#8884A8] rounded hover:border-[#8884A8] hover:text-[#E8E6F2] transition-colors"
            >
              <PlusCircle size={12} /> Add to Corpus
            </button>
            <button
              onClick={async () => {
                setSubmitted(true);
                try {
                  await api.cases.submitEvidence(CASE_ID, {
                    module_id: "shadowtrace",
                    verdict: {
                      attributed_author: "d4rk_exch4nger",
                      platform: "AlphaBay / Telegram",
                      confidence: 0.87,
                      signals: { lexical: 0.91, syntactic: 0.84, temporal: 0.79 },
                      inferred_timezone: "UTC+5:30 (IST)",
                      peak_hours_utc: [1, 2, 3, 4, 21, 22, 23],
                    },
                    confidence: 0.87,
                    artifacts: [
                      {
                        artifact_id: crypto.randomUUID(),
                        artifact_type: "features",
                        uri: "s3://shadowtrace-corpus/fingerprints/sample_0035.json",
                        sha256: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
                      },
                    ],
                  });
                } catch {}
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                submitted
                  ? "bg-[#2A9D4E]/20 border border-[#2A9D4E] text-[#2A9D4E]"
                  : "bg-[#F0A500] text-[#0D0B14] hover:bg-[#F0A500]/90"
              }`}
            >
              <Send size={12} /> {submitted ? "Evidence Submitted & Hashed" : "Submit Evidence"}
            </button>
          </div>
        </div>

        {/* Add to Corpus Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
            <div className="bg-[#13111E] border border-[#2A2640] rounded-lg p-6 max-w-lg w-full shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-[#E8E6F2]">Add Known Actor / Sample to Corpus</h3>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="text-[#8884A8] hover:text-white text-xs font-mono"
                >
                  ✕
                </button>
              </div>

              {addSuccess ? (
                <div className="p-4 bg-[#2A9D4E]/20 border border-[#2A9D4E] text-[#2A9D4E] text-xs rounded text-center font-medium">
                  ✓ Sample indexed to pgvector & actor network updated!
                </div>
              ) : (
                <form onSubmit={handleAddSample} className="flex flex-col gap-3">
                  <div>
                    <label className="block text-[10px] text-[#8884A8] mb-1">Actor Handle / ID</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. shadow_broker_99"
                      value={actorHandle}
                      onChange={(e) => setActorHandle(e.target.value)}
                      className="w-full bg-[#1C1929] border border-[#2A2640] rounded px-3 py-1.5 text-xs text-[#E8E6F2] font-mono focus:border-[#F0A500] outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] text-[#8884A8] mb-1">Platform</label>
                      <select
                        value={platform}
                        onChange={(e) => setPlatform(e.target.value)}
                        className="w-full bg-[#1C1929] border border-[#2A2640] rounded px-3 py-1.5 text-xs text-[#E8E6F2] font-mono focus:border-[#F0A500] outline-none"
                      >
                        <option value="AlphaBay / Telegram">AlphaBay / Telegram</option>
                        <option value="Hansa / IRC">Hansa / IRC</option>
                        <option value="Empire Market">Empire Market</option>
                        <option value="BreachForums">BreachForums</option>
                        <option value="Dread">Dread</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] text-[#8884A8] mb-1">Observed Hour (UTC)</label>
                      <select
                        value={activityHour}
                        onChange={(e) => setActivityHour(e.target.value)}
                        className="w-full bg-[#1C1929] border border-[#2A2640] rounded px-3 py-1.5 text-xs text-[#E8E6F2] font-mono focus:border-[#F0A500] outline-none"
                      >
                        {Array.from({ length: 24 }, (_, i) => (
                          <option key={i} value={String(i).padStart(2, "0")}>
                            {String(i).padStart(2, "0")}:00 UTC
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] text-[#8884A8] mb-1">Text Sample (Stylometry extraction)</label>
                    <textarea
                      required
                      rows={4}
                      placeholder="Paste actor message, forum post, ransom note, or listing description..."
                      value={sampleText}
                      onChange={(e) => setSampleText(e.target.value)}
                      className="w-full bg-[#1C1929] border border-[#2A2640] rounded px-3 py-1.5 text-xs text-[#E8E6F2] font-mono focus:border-[#F0A500] outline-none resize-none"
                    />
                  </div>

                  <div className="flex justify-end gap-2 mt-2">
                    <button
                      type="button"
                      onClick={() => setShowAddModal(false)}
                      className="px-3 py-1.5 text-xs border border-[#2A2640] text-[#8884A8] rounded hover:border-[#8884A8]"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-1.5 text-xs font-medium bg-[#F0A500] text-[#0D0B14] rounded hover:bg-[#F0A500]/90"
                    >
                      Index & Update Centroid
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Two-column layout: 55% / 45% */}
        <main className="flex-1 overflow-y-auto p-4">
          <div className="flex gap-4 h-full min-h-0">

            {/* ── Left column (55%) ──────────────────────────────── */}
            <div className="flex flex-col gap-4" style={{ flex: "0 0 55%" }}>

              {/* 1. Text Sample Input */}
              <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
                <h2 className="text-sm font-medium mb-2">Text Sample Input</h2>
                <div className="bg-[#1C1929] border border-[#2A2640] rounded p-3 font-mono text-xs text-[#E8E6F2] leading-relaxed whitespace-pre-wrap">
                  {SAMPLE_TEXT}
                </div>
                <p className="mt-2 font-mono text-[10px] text-[#4A4768]">
                  Source: AlphaBay Archive&nbsp;&nbsp;|&nbsp;&nbsp;Platform: Dark Web Forum&nbsp;&nbsp;|&nbsp;&nbsp;Timestamp: 2026-08-14 02:17 UTC
                </p>
              </div>

              {/* 2. Linguistic Fingerprint Radar */}
              <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
                <h2 className="text-sm font-medium mb-3">Fingerprint Analysis</h2>
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={RADAR_DATA} cx="50%" cy="50%" outerRadius="75%">
                      <PolarGrid stroke="#2A2640" />
                      <PolarAngleAxis
                        dataKey="axis"
                        tick={{ fill: "#4A4768", fontSize: 10, fontFamily: "Space Grotesk, sans-serif" }}
                      />
                      <Radar
                        dataKey="value"
                        stroke="#6B4FFF"
                        fill="#6B4FFF"
                        fillOpacity={0.3}
                        dot={{ fill: "#6B4FFF", r: 3 }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                {/* Key features */}
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2 border-t border-[#2A2640] pt-3">
                  {[
                    ["Type-token ratio", "0.61"],
                    ["Avg sentence length", "8.2 tokens"],
                    ["Punctuation rate", "0.04/sentence"],
                    ["Typo rate", "0.08"],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between font-mono text-[11px]">
                      <span className="text-[#4A4768]">{k}</span>
                      <span className="text-[#E8E6F2]">{v}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 3. Temporal Activity Profile */}
              <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
                <h2 className="text-sm font-medium mb-1">Temporal Activity Profile</h2>
                <p className="text-[10px] text-[#4A4768] mb-3">Posting Activity by Hour (UTC)</p>
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={HOURLY} barSize={4} barGap={2} margin={{ top: 0, right: 0, left: -24, bottom: 0 }}>
                      <XAxis
                        dataKey="h"
                        tick={{ fill: "#4A4768", fontSize: 9, fontFamily: "JetBrains Mono, monospace" }}
                        tickFormatter={(h) => h % 4 === 0 ? `${String(h).padStart(2,"0")}` : ""}
                        axisLine={false} tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{ background: "#1C1929", border: "1px solid #2A2640", borderRadius: 4, fontSize: 10 }}
                        labelFormatter={(h) => `${String(h).padStart(2,"0")}:00 UTC`}
                        formatter={(v: number) => [v, "posts"]}
                        cursor={{ fill: "#2A2640" }}
                      />
                      <ReferenceLine x={2} stroke="#F0A500" strokeDasharray="3 3" label={{ value: "Peak", fill: "#F0A500", fontSize: 9, position: "top" }} />
                      <Bar dataKey="v" radius={[1, 1, 0, 0]}>
                        {HOURLY.map(({ h }) => (
                          <Cell
                            key={h}
                            fill={(h >= 1 && h <= 4) || (h >= 21 && h <= 23) ? "#6B4FFF" : "#2A2640"}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-[10px] text-[#8884A8] mt-1 font-mono">
                  Inferred timezone: UTC+5:30 (IST) — confidence 73%
                </p>
              </div>
            </div>

            {/* ── Right column (45%) ─────────────────────────────── */}
            <div className="flex flex-col gap-4 flex-1 min-w-0">

              {/* 1. Attribution Results */}
              <div className="bg-[#13111E] border border-[#2A2640] border-l-[#F0A500] rounded p-4"
                style={{ borderLeftWidth: "4px", borderLeftColor: "#F0A500" }}>
                <h2 className="text-sm font-semibold mb-3">Top Matches</h2>

                <div className="flex flex-col gap-2">
                  {MATCHES.map((m) => (
                    <div
                      key={m.rank}
                      className="rounded p-3 border"
                      style={{
                        backgroundColor: m.highlighted ? "#2A210015" : "#1C1929",
                        borderColor: m.highlighted ? "#F0A50040" : "#2A2640",
                      }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className="w-5 h-5 rounded-sm flex items-center justify-center text-[10px] font-bold shrink-0"
                          style={{
                            backgroundColor: m.highlighted ? "#F0A500" : "#2A2640",
                            color: m.highlighted ? "#0D0B14" : "#4A4768",
                          }}
                        >
                          {m.rank}
                        </span>
                        <span className="font-mono text-sm font-medium text-[#E8E6F2]">{m.handle}</span>
                        <span className="ml-auto text-[10px] text-[#4A4768]">{m.platform}</span>
                      </div>

                      <ConfBar
                        value={m.confidence}
                        color={m.highlighted ? "#F0A500" : m.confidence > 50 ? "#6B4FFF" : "#4A4768"}
                      />

                      <div className="mt-2 text-[10px] text-[#4A4768] font-mono">
                        Lexical: {m.signals.lex}% | Syntactic: {m.signals.syn}% | Temporal: {m.signals.temp}%
                      </div>

                      {m.crossPlatform && (
                        <p className="mt-1 text-[10px] text-[#2A9D4E]">{m.crossPlatform}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 2. Actor Network Graph */}
              <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-sm font-medium">Actor Network Graph</h2>
                  <button className="flex items-center gap-1 text-[10px] text-[#F0A500] hover:underline">
                    <ExternalLink size={10} /> Expand in full view
                  </button>
                </div>
                <ActorGraph />
              </div>

              {/* 3. Cross-Module Signal */}
              <div className="bg-[#13111E] border border-[#2A2640] border-l-[#F0A500] rounded p-4"
                style={{ borderLeftWidth: "4px", borderLeftColor: "#F0A500" }}>
                <div className="flex items-center gap-2 mb-3">
                  <h2 className="text-sm font-medium">Cross-Module Signal</h2>
                  <span className="px-2 py-0.5 bg-[#F0A500]/15 border border-[#F0A500]/40 text-[#F0A500] text-[10px] font-medium rounded-sm">
                    ChainEye Correlation Detected
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    ["Timezone overlap",       "IST (UTC+5:30) — match", "#2A9D4E"],
                    ["Activity overlap score", "0.78",                    "#F0A500"],
                    ["Operational period",     "Overlap: Jul–Aug 2026",   "#E8E6F2"],
                  ].map(([label, value, color]) => (
                    <div key={label as string} className="bg-[#1C1929] rounded p-2">
                      <span className="text-[#4A4768] text-[10px] block">{label as string}</span>
                      <span className="font-mono text-xs font-medium" style={{ color: color as string }}>{value as string}</span>
                    </div>
                  ))}
                </div>

                <button className="mt-3 text-[11px] text-[#F0A500] hover:underline flex items-center gap-1">
                  <ExternalLink size={10} /> View Convergence Report
                </button>
              </div>

            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
