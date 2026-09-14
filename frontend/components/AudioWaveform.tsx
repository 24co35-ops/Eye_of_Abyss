"use client";

import { useEffect, useRef, useCallback } from "react";
import WaveSurfer from "wavesurfer.js";

export interface Segment {
  start: number; // seconds
  end: number;
  verdict: "REAL" | "SYNTHETIC";
  confidence: number;
}

interface Props {
  audioUrl?: string;
  segments: Segment[];
  duration: number; // seconds
  onReady?: (ws: WaveSurfer) => void;
}

// Time labels for the timeline
const TIME_LABELS = ["00:00", "00:30", "01:00", "01:30", "02:00", "02:14"];

export default function AudioWaveform({ audioUrl, segments, duration, onReady }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);

  const initWaveSurfer = useCallback(() => {
    if (!containerRef.current) return;
    if (wsRef.current) { wsRef.current.destroy(); wsRef.current = null; }

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#8884A8",
      progressColor: "#F0A500",
      cursorColor: "#F0A500",
      cursorWidth: 2,
      height: 80,
      barWidth: 2,
      barGap: 1,
      barRadius: 1,
      normalize: true,
      interact: true,
    });

    wsRef.current = ws;
    ws.on("ready", () => onReady?.(ws));

    if (audioUrl) {
      ws.load(audioUrl);
    } else {
      // Synthetic waveform data for demo — 200 random bars
      const fake = new Float32Array(200).map(() => Math.random() * 0.8 + 0.1);
      ws.load("", [fake]);
    }
  }, [audioUrl, onReady]);

  useEffect(() => {
    initWaveSurfer();
    return () => { wsRef.current?.destroy(); wsRef.current = null; };
  }, [initWaveSurfer]);

  // Segment highlights as percentage overlays
  const highlights = segments.map((seg) => ({
    left: `${(seg.start / duration) * 100}%`,
    width: `${((seg.end - seg.start) / duration) * 100}%`,
    color: seg.verdict === "SYNTHETIC" ? "rgba(201,42,42,0.25)" : "rgba(42,157,78,0.25)",
    border: seg.verdict === "SYNTHETIC" ? "#C92A2A" : "#2A9D4E",
  }));

  // Confidence track: split into 20 slots
  const confidenceSlots = Array.from({ length: 20 }, (_, i) => {
    const t = (i / 20) * duration;
    const seg = segments.find((s) => t >= s.start && t < s.end);
    if (!seg) return "#2A2640";
    if (seg.verdict === "SYNTHETIC") return seg.confidence > 0.9 ? "#C92A2A" : "#8B1A1A";
    return seg.verdict === "REAL" ? "#2A9D4E" : "#F0A500";
  });

  return (
    <div className="flex flex-col gap-2">
      {/* Waveform with segment overlays */}
      <div className="relative">
        {/* Segment highlight overlays — sit above the waveform canvas */}
        <div className="absolute inset-0 pointer-events-none z-10 flex">
          {highlights.map((h, i) => (
            <div
              key={i}
              className="absolute top-0 bottom-0"
              style={{
                left: h.left,
                width: h.width,
                backgroundColor: h.color,
                borderLeft: `1px solid ${h.border}`,
                borderRight: `1px solid ${h.border}`,
              }}
            />
          ))}
        </div>
        {/* Playhead marker at ~60% */}
        <div
          className="absolute top-0 bottom-0 z-20 pointer-events-none"
          style={{ left: "60%", width: "2px", backgroundColor: "#F0A500" }}
        />
        <div ref={containerRef} className="w-full" />
      </div>

      {/* Timeline labels */}
      <div className="flex justify-between px-0">
        {TIME_LABELS.map((t) => (
          <span key={t} className="text-[10px] font-mono text-[#4A4768]">{t}</span>
        ))}
      </div>

      {/* Confidence track */}
      <div className="flex gap-0.5 h-2 mt-1">
        {confidenceSlots.map((color, i) => (
          <div key={i} className="flex-1 rounded-sm" style={{ backgroundColor: color }} />
        ))}
      </div>
      <div className="flex justify-between">
        <span className="text-[10px] text-[#4A4768]">Confidence track</span>
        <div className="flex gap-3 text-[10px] text-[#4A4768]">
          <span><span className="inline-block w-2 h-2 rounded-sm bg-[#2A9D4E] mr-1" />Real</span>
          <span><span className="inline-block w-2 h-2 rounded-sm bg-[#C92A2A] mr-1" />Synthetic</span>
          <span><span className="inline-block w-2 h-2 rounded-sm bg-[#F0A500] mr-1" />Uncertain</span>
        </div>
      </div>
    </div>
  );
}
