"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { NavRail } from "@/components/NavRail";
import { TopBar } from "@/components/TopBar";
import MelSpectrogram from "@/components/MelSpectrogram";
import type { Segment } from "@/components/AudioWaveform";
import {
  Mic,
  MicOff,
  Upload,
  Square,
  Save,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from "lucide-react";

// WaveSurfer uses browser APIs — must be client-only
const AudioWaveform = dynamic(() => import("@/components/AudioWaveform"), { ssr: false });

// ── Mock data — Prompt 3 exact spec ────────────────────────────────────────
const CASE_ID = "EOA-2026-0037";
const DURATION = 134; // 2m 14s

const MOCK_SEGMENTS: Segment[] = [
  { start: 8,  end: 20,  verdict: "REAL",      confidence: 0.94 },
  { start: 23, end: 31,  verdict: "SYNTHETIC", confidence: 0.96 },
  { start: 45, end: 67,  verdict: "SYNTHETIC", confidence: 0.89 },
  { start: 72, end: 87,  verdict: "SYNTHETIC", confidence: 0.91 },
  { start: 91, end: 134, verdict: "REAL",      confidence: 0.87 },
];

const SEGMENT_TABLE = [
  { time: "00:08", dur: "12s", verdict: "REAL",      conf: "94%", type: "Clean speech" },
  { time: "00:23", dur: "8s",  verdict: "SYNTHETIC", conf: "96%", type: "TTS" },
  { time: "00:45", dur: "22s", verdict: "SYNTHETIC", conf: "89%", type: "Voice conversion" },
  { time: "01:12", dur: "15s", verdict: "SYNTHETIC", conf: "91%", type: "TTS" },
  { time: "01:31", dur: "43s", verdict: "REAL",      conf: "87%", type: "Clean speech" },
];

type AnalysisState = "idle" | "uploading" | "analyzing" | "done";

const VG_WS = (process.env.NEXT_PUBLIC_VOICEGUARD_URL ?? "http://localhost:8001").replace("http", "ws");
const VG_HTTP = process.env.NEXT_PUBLIC_VOICEGUARD_URL ?? "http://localhost:8001";

async function analyzeFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  // ponytail: fire-and-forget; errors fall through to mock
  await fetch(`${VG_HTTP}/analyze/file`, { method: "POST", body: form }).catch(() => {});
}

export default function VoiceGuardPage() {
  const [state, setState] = useState<AnalysisState>("done"); // demo starts post-analysis
  const [elapsed, setElapsed] = useState(134);
  const [liveMode, setLiveMode] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | undefined>(undefined);
  const [attached, setAttached] = useState(false);
  // TopBar requires these even though we don't use context panel here
  const [contextOpen] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fmtTime = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  const startTimer = useCallback(() => {
    setElapsed(0);
    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const handleFile = useCallback(async (file: File) => {
    setAudioUrl(URL.createObjectURL(file));
    setState("uploading");
    startTimer();
    await analyzeFile(file);
    setState("analyzing");
    setTimeout(() => { setState("done"); stopTimer(); }, 2000);
  }, [startTimer, stopTimer]);

  const toggleLive = useCallback(() => {
    if (liveMode) {
      wsRef.current?.close(); wsRef.current = null;
      setLiveMode(false); setState("done"); stopTimer();
    } else {
      setLiveMode(true); setState("analyzing"); startTimer();
      try {
        const ws = new WebSocket(`${VG_WS}/analyze/stream`);
        ws.onerror = () => { setState("done"); setLiveMode(false); stopTimer(); };
        wsRef.current = ws;
      } catch { setState("done"); setLiveMode(false); stopTimer(); }
    }
  }, [liveMode, startTimer, stopTimer]);

  const stopAnalysis = useCallback(() => {
    wsRef.current?.close(); wsRef.current = null;
    stopTimer(); setLiveMode(false); setState("done");
  }, [stopTimer]);

  useEffect(() => () => { stopTimer(); wsRef.current?.close(); }, [stopTimer]);

  const isLive = state === "analyzing" || liveMode;
  const isDone = state === "done";

  return (
    <div className="flex h-screen bg-[#0D0B14] text-[#E8E6F2] overflow-hidden">
      <NavRail activeItem="voiceguard" />

      <div className="flex flex-col flex-1 overflow-hidden">
        {/* TopBar — VoiceGuard screen has no context panel, pass no-op */}
        <TopBar
          onToggleContext={() => {}}
          isContextOpen={contextOpen}
          activeCaseId={CASE_ID}
        />

        {/* Breadcrumb + action buttons below topbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#2A2640] bg-[#0D0B14]">
          <nav className="flex items-center gap-1.5 text-xs text-[#4A4768]">
            <span>Cases</span>
            <span>/</span>
            <span className="font-mono text-[#8884A8]">{CASE_ID}</span>
            <span>/</span>
            <span className="text-[#E8E6F2]">VoiceGuard</span>
          </nav>
          <div className="flex gap-2">
            <button
              onClick={stopAnalysis}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-[#C92A2A] text-[#C92A2A] rounded hover:bg-[#C92A2A]/10 transition-colors"
            >
              <Square size={12} /> Stop Analysis
            </button>
            <button
              disabled={!isDone}
              onClick={() => setAttached(true)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                isDone && !attached
                  ? "bg-[#F0A500] text-[#0D0B14] hover:bg-[#F0A500]/90"
                  : "bg-[#2A2640] text-[#4A4768] cursor-not-allowed"
              }`}
            >
              <Save size={12} /> {attached ? "Saved" : "Save Evidence"}
            </button>
          </div>
        </div>

        {/* Main — single centered column per spec */}
        <main className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 max-w-5xl mx-auto w-full">

          {/* ── Live Status Banner ──────────────────────────────────── */}
          <div className="flex items-center justify-between px-4 py-3 bg-[#1C1929] border border-[#2A2640] rounded">
            <div className="flex items-center gap-2">
              {isLive ? (
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute h-full w-full rounded-full bg-[#C92A2A] opacity-75" />
                  <span className="relative h-2.5 w-2.5 rounded-full bg-[#C92A2A]" />
                </span>
              ) : (
                <CheckCircle2 size={12} className="text-[#2A9D4E]" />
              )}
              <span className="text-xs font-medium">
                {isLive
                  ? `LIVE ANALYSIS — ${fmtTime(elapsed)} elapsed`
                  : `ANALYSIS COMPLETE — ${fmtTime(elapsed)} duration`}
              </span>
            </div>

            <span className="text-xs text-[#8884A8]">{CASE_ID} — Vishing Call Recording</span>

            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 bg-[#C92A2A] text-white text-xs font-semibold rounded-sm">
                SYNTHETIC DETECTED
              </span>
              <span className="font-mono text-sm text-[#F0A500]">91.4%</span>
            </div>
          </div>

          {/* ── Upload / Live controls ──────────────────────────────── */}
          {state === "idle" ? (
            <div
              className="border-2 border-dashed border-[#2A2640] rounded p-8 flex flex-col items-center gap-4 bg-[#13111E] cursor-pointer hover:border-[#F0A500]/50 transition-colors"
              onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={32} className="text-[#4A4768]" />
              <p className="text-sm text-[#8884A8]">Drop a call recording here or click to upload</p>
              <p className="text-xs text-[#4A4768]">WAV · MP3 · FLAC · OGG</p>
              <input ref={fileInputRef} type="file" accept="audio/*" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
              <button
                onClick={(e) => { e.stopPropagation(); toggleLive(); }}
                className="flex items-center gap-2 px-4 py-2 bg-[#C92A2A]/20 border border-[#C92A2A] text-[#C92A2A] text-xs font-medium rounded hover:bg-[#C92A2A]/30 transition-colors"
              >
                <Mic size={14} /> Start Live Stream
              </button>
            </div>
          ) : (
            <div className="flex justify-end gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-[#2A2640] text-[#8884A8] rounded hover:border-[#F0A500] hover:text-[#F0A500] transition-colors"
              >
                <Upload size={12} /> Upload File
              </button>
              <input ref={fileInputRef} type="file" accept="audio/*" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
              <button
                onClick={toggleLive}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded transition-colors ${
                  liveMode
                    ? "border-[#C92A2A] text-[#C92A2A] bg-[#C92A2A]/10"
                    : "border-[#2A2640] text-[#8884A8] hover:border-[#C92A2A] hover:text-[#C92A2A]"
                }`}
              >
                {liveMode ? <><MicOff size={12} /> Stop Stream</> : <><Mic size={12} /> Live Stream</>}
              </button>
            </div>
          )}

          {/* ── Waveform Panel ──────────────────────────────────────── */}
          <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium">Audio Waveform</h2>
              <div className="flex items-center gap-1.5 text-[10px] text-[#4A4768]">
                <Clock size={10} />
                <span className="font-mono">{fmtTime(elapsed)}</span>
              </div>
            </div>
            <AudioWaveform audioUrl={audioUrl} segments={MOCK_SEGMENTS} duration={DURATION} />
          </div>

          {/* ── Segment Analysis + Spectral Analysis ─────────────────── */}
          <div className="grid grid-cols-2 gap-4">

            {/* Segment table */}
            <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
              <h2 className="text-sm font-medium mb-3">Segment Analysis</h2>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[#2A2640]">
                    {["Time", "Dur", "Verdict", "Conf", "Type"].map((h) => (
                      <th key={h} className="text-left pb-2 text-[#4A4768] font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SEGMENT_TABLE.map((row, i) => (
                    <tr key={i} className="border-b border-[#2A2640]/40 hover:bg-[#1C1929] transition-colors">
                      <td className="py-2 font-mono text-[#E8E6F2]">{row.time}</td>
                      <td className="py-2 font-mono text-[#8884A8]">{row.dur}</td>
                      <td className="py-2">
                        <span className="px-1.5 py-0.5 rounded-sm text-[10px] font-semibold"
                          style={{
                            color: row.verdict === "SYNTHETIC" ? "#C92A2A" : "#2A9D4E",
                            backgroundColor: row.verdict === "SYNTHETIC" ? "#C92A2A1A" : "#2A9D4E1A",
                          }}>
                          {row.verdict}
                        </span>
                      </td>
                      <td className="py-2 font-mono">{row.conf}</td>
                      <td className="py-2 text-[#8884A8]">{row.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Spectral analysis */}
            <div className="bg-[#13111E] border border-[#2A2640] rounded p-4">
              <h2 className="text-sm font-medium mb-0.5">Spectral Analysis</h2>
              <p className="text-[10px] text-[#4A4768] mb-3">Mel Spectrogram — Synthetic segment 00:23</p>
              <MelSpectrogram />
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="bg-[#1C1929] rounded p-2">
                  <span className="text-[10px] text-[#4A4768] block">GAN artifact signature</span>
                  <span className="font-mono text-xs font-medium text-[#C92A2A]">Detected</span>
                </div>
                <div className="bg-[#1C1929] rounded p-2">
                  <span className="text-[10px] text-[#4A4768] block">Spectral flatness delta</span>
                  <span className="font-mono text-xs font-medium text-[#F0A500]">+0.34</span>
                  <span className="text-[9px] text-[#4A4768] ml-1">(anomalous)</span>
                </div>
              </div>
            </div>
          </div>

          {/* ── Evidence Summary ────────────────────────────────────── */}
          <div className="bg-[#1C1929] border border-[#2A2640] border-l-[#F0A500] rounded p-4"
            style={{ borderLeftWidth: "4px", borderLeftColor: "#F0A500" }}>
            <h2 className="text-sm font-semibold mb-3">Analysis Summary</h2>

            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={16} className="text-[#C92A2A] shrink-0" />
              <span className="text-base font-semibold text-[#C92A2A]">
                SYNTHETIC — AI-generated voice detected
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <span className="text-[10px] text-[#4A4768] block mb-0.5">Overall Confidence</span>
                <span className="font-mono text-lg font-medium">91.4%</span>
                <div className="mt-1 h-1 bg-[#2A2640] rounded-full">
                  <div className="h-1 bg-[#C92A2A] rounded-full" style={{ width: "91.4%" }} />
                </div>
              </div>
              <div>
                <span className="text-[10px] text-[#4A4768] block mb-0.5">Synthetic Duration</span>
                <span className="font-mono text-sm">1m 02s</span>
                <span className="text-[10px] text-[#4A4768]"> / 2m 14s total</span>
                <p className="text-[10px] text-[#C92A2A] mt-0.5">46% synthetic</p>
              </div>
              <div>
                <span className="text-[10px] text-[#4A4768] block mb-0.5">Detected Types</span>
                <p className="text-xs">TTS (2 segments)</p>
                <p className="text-xs text-[#8884A8]">Voice Conversion (1 segment)</p>
              </div>
            </div>

            <div className="flex gap-6 text-[11px] text-[#4A4768] font-mono mb-4">
              <span>Model: DistilWav2Vec2 + ECAPA-TDNN ensemble</span>
              <span>Inference: 162ms avg/chunk</span>
            </div>

            <button
              onClick={() => setAttached(true)}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-medium rounded transition-colors ${
                attached
                  ? "bg-[#2A9D4E]/20 border border-[#2A9D4E] text-[#2A9D4E]"
                  : "bg-[#F0A500] text-[#0D0B14] hover:bg-[#F0A500]/90"
              }`}
            >
              {attached
                ? <><CheckCircle2 size={14} /> Attached to {CASE_ID}</>
                : `Attach to Case ${CASE_ID}`}
            </button>
          </div>

        </main>
      </div>
    </div>
  );
}
