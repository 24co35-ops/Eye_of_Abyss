"use client";

import { useEffect, useRef } from "react";

// Draws a synthetic mel-spectrogram heatmap on a canvas.
// Colors: deep purple (#1C1929) → indigo (#6B4FFF) → amber (#F0A500)
export default function MelSpectrogram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;

    // Gradient palette: dark → indigo → amber
    const palette = (v: number): string => {
      // v in [0, 1]
      if (v < 0.4) {
        // dark → indigo
        const t = v / 0.4;
        const r = Math.round(28 + t * (107 - 28));
        const g = Math.round(25 + t * (79 - 25));
        const b = Math.round(41 + t * (255 - 41));
        return `rgb(${r},${g},${b})`;
      } else {
        // indigo → amber
        const t = (v - 0.4) / 0.6;
        const r = Math.round(107 + t * (240 - 107));
        const g = Math.round(79 + t * (165 - 79));
        const b = Math.round(255 + t * (0 - 255));
        return `rgb(${r},${g},${b})`;
      }
    };

    // Seed a pseudo-random mel spectrogram pattern
    const cols = 80;
    const rows = 40;
    const cw = W / cols;
    const ch = H / rows;

    // Simple deterministic noise using sine harmonics
    for (let col = 0; col < cols; col++) {
      for (let row = 0; row < rows; row++) {
        const freq = (rows - row) / rows; // high freq at top
        const time = col / cols;

        // Base energy envelope — simulate formants
        let v =
          0.3 * Math.abs(Math.sin(freq * Math.PI * 4 + time * 6)) +
          0.2 * Math.abs(Math.sin(freq * Math.PI * 8 + time * 12)) +
          0.15 * Math.abs(Math.sin(freq * Math.PI * 2.5 + time * 3));

        // GAN artifact: anomalous high-energy band in mid-freq
        if (freq > 0.35 && freq < 0.55) v = Math.min(1, v + 0.35);

        // Low-freq rumble
        if (freq < 0.15) v = Math.min(1, v + 0.25 * Math.abs(Math.sin(time * 8)));

        ctx.fillStyle = palette(Math.min(1, v));
        ctx.fillRect(col * cw, row * ch, cw, ch);
      }
    }

    // Frequency axis labels (left)
    ctx.fillStyle = "#4A4768";
    ctx.font = "9px JetBrains Mono, monospace";
    const freqLabels = ["8k", "4k", "2k", "1k", "500", "250", "125"];
    freqLabels.forEach((label, i) => {
      ctx.fillText(label, 2, (i / (freqLabels.length - 1)) * H + 9);
    });
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={560}
      height={140}
      className="w-full rounded"
      style={{ imageRendering: "pixelated" }}
    />
  );
}
