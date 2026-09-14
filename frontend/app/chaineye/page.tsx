"use client";

import React, { useState } from "react";
import Link from "next/link";
import { NavRail } from "@/components/NavRail";
import { WalletClusterGraph } from "@/components/WalletClusterGraph";
import { TransactionTimeline } from "@/components/TransactionTimeline";
import {
  ShieldCheck,
  Lock,
  Send,
  AlertTriangle,
  ExternalLink,
  ChevronRight,
  FileCheck,
  Activity,
  Layers,
  CheckCircle2,
  Clock,
} from "lucide-react";

export default function ChainEyeInvestigationView() {
  const [isEvidenceSubmitted, setIsEvidenceSubmitted] = useState(false);
  const [isFreezeDraftOpen, setIsFreezeDraftOpen] = useState(false);

  const handleEvidenceSubmit = () => {
    setIsEvidenceSubmitted(true);
  };

  return (
    <div className="flex h-screen w-screen bg-abyss text-text-primary overflow-hidden font-sans select-none">
      {/* Left Navigation Rail: 56px wide (ChainEye Active) */}
      <NavRail activeItem="chaineye" />

      {/* Main Layout Container */}
      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
        
        {/* Top Bar (48px height): Breadcrumb + Action Controls */}
        <header className="h-[48px] min-h-[48px] bg-void border-b border-mist px-4 flex items-center justify-between z-20 select-none">
          {/* Breadcrumb: "Cases / EOA-2026-0041 / ChainEye" in Space Grotesk */}
          <div className="flex items-center gap-2 text-xs">
            <Link href="/" className="text-text-muted hover:text-text-secondary transition-colors">
              Cases
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
            <Link href="/" className="font-mono text-gaze hover:underline">
              EOA-2026-0041
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
            <span className="font-medium text-text-primary">ChainEye Forensics</span>
          </div>

          {/* Right Controls: Submit Evidence & Anchor Button */}
          <div className="flex items-center gap-2.5">
            {/* Submit Evidence Button (Amber filled, 4px radius) */}
            <button
              onClick={handleEvidenceSubmit}
              className={`px-3 py-1 rounded-[4px] text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                isEvidenceSubmitted
                  ? "bg-safe text-abyss cursor-default"
                  : "bg-gaze hover:bg-gaze/90 text-abyss shadow-none"
              }`}
            >
              {isEvidenceSubmitted ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Evidence Submitted</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Evidence</span>
                </>
              )}
            </button>

            {/* Anchor Button (Indigo outlined, disabled until supervisor approves) */}
            <button
              disabled
              title="Disabled until supervisor approval"
              className="px-3 py-1 rounded-[4px] border border-signal text-signal opacity-45 cursor-not-allowed text-xs font-mono flex items-center gap-1.5 bg-transparent"
            >
              <Lock className="w-3.5 h-3.5 text-signal" />
              <span>Anchor (Supervisor Req.)</span>
            </button>
          </div>
        </header>

        {/* Content Body: Two columns (65% / 35%) + 320px Right Context Panel */}
        <div className="flex-1 flex overflow-hidden">
          
          {/* Main Grid Workspace */}
          <main className="flex-1 overflow-y-auto p-4">
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
              
              {/* LEFT COLUMN (65% width on xl): Wallet Graph + Transaction Timeline */}
              <div className="xl:col-span-8 space-y-4">
                
                {/* Wallet Cluster Graph Panel */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-medium text-text-primary tracking-tight">
                      Wallet Cluster Graph
                    </h2>
                    <span className="text-[10px] font-mono text-text-muted">
                      CO-SPEND &amp; PEELING CHAIN ANALYSIS (DEPTH: 3)
                    </span>
                  </div>

                  {/* Cytoscape.js Graph Canvas */}
                  <WalletClusterGraph suspectAddress="1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2" />
                </div>

                {/* Horizontal Transaction Timeline Strip */}
                <TransactionTimeline />
              </div>

              {/* RIGHT COLUMN (35% width on xl): Analysis Panel */}
              <div className="xl:col-span-4 space-y-3.5">
                
                {/* Section 1: "VASP Attribution" Card (#1C1929 bg) */}
                <div className="bg-shadow border border-mist rounded-[4px] p-3.5 space-y-2.5">
                  <div className="flex items-center justify-between border-b border-mist pb-2">
                    <div className="text-xs font-semibold text-text-primary tracking-tight">
                      VASP Attribution
                    </div>
                    <span className="text-[10px] font-mono text-signal font-semibold">
                      82% MATCH
                    </span>
                  </div>

                  {/* VASP Entity */}
                  <div className="space-y-1">
                    <span className="text-[12px] text-text-secondary block">VASP Entity:</span>
                    <span className="text-[15px] font-medium text-text-primary block font-sans">
                      Binance Global
                    </span>
                  </div>

                  {/* Confidence Bar in Indigo */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-mono text-text-muted">
                      <span>CONFIDENCE METRIC</span>
                      <span className="text-signal">82%</span>
                    </div>
                    <div className="w-full h-1.5 bg-void rounded-none overflow-hidden">
                      <div className="h-full bg-signal" style={{ width: "82%" }} />
                    </div>
                  </div>

                  {/* Metadata Grid */}
                  <div className="grid grid-cols-2 gap-2 pt-1 border-t border-mist/60 text-xs font-sans">
                    <div>
                      <span className="text-[11px] text-text-secondary block">Sub-accounts:</span>
                      <span className="text-[13px] font-medium text-text-primary font-mono">3 detected</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-text-secondary block">KYC Status:</span>
                      <span className="text-[12px] text-threat font-medium">Subpoena Required</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-[11px] text-text-secondary block">Jurisdiction:</span>
                      <span className="text-[13px] font-medium text-text-primary">Cayman Islands</span>
                    </div>
                  </div>
                </div>

                {/* Section 2: "Withdrawal Prediction" Card (Amber Left Border) */}
                <div className="bg-shadow border border-mist border-l-2 border-l-gaze rounded-[4px] p-3.5 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-primary tracking-tight">
                      Withdrawal Prediction
                    </span>
                    <span className="px-2 py-0.5 rounded-[2px] bg-gaze/15 border border-gaze/30 text-gaze font-mono text-[10px] font-bold">
                      ACTION REQUIRED
                    </span>
                  </div>

                  {/* Predicted Window */}
                  <div>
                    <span className="text-[11px] text-text-secondary block font-mono">
                      PREDICTED WITHDRAWAL WINDOW:
                    </span>
                    <span className="text-[18px] font-semibold text-gaze block leading-tight font-sans mt-0.5">
                      Sep 16, 02:00–04:00 UTC
                    </span>
                  </div>

                  {/* Confidence Bar in Indigo */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-mono text-text-muted">
                      <span>PREDICTION CONFIDENCE</span>
                      <span className="text-signal">74%</span>
                    </div>
                    <div className="w-full h-1.5 bg-void rounded-none overflow-hidden">
                      <div className="h-full bg-signal" style={{ width: "74%" }} />
                    </div>
                  </div>

                  {/* Basis */}
                  <div className="text-[11px] text-text-secondary bg-void border border-mist p-2 rounded-[2px]">
                    <span className="text-text-muted font-mono block text-[9px]">HEURISTIC BASIS:</span>
                    Dormancy cycle day 12/14 — matches T2 withdrawal pattern
                  </div>

                  {/* Button: "Draft Freeze Request" (Amber filled) */}
                  <button
                    onClick={() => setIsFreezeDraftOpen(true)}
                    className="w-full py-2 bg-gaze hover:bg-gaze/90 text-abyss font-semibold rounded-[4px] text-xs transition-colors flex items-center justify-center gap-1.5 shadow-none"
                  >
                    <FileCheck className="w-3.5 h-3.5" />
                    <span>Draft Freeze Request</span>
                  </button>
                </div>

                {/* Section 3: "Wallet Statistics" (Monospace Data Table) */}
                <div className="bg-shadow border border-mist rounded-[4px] p-3.5 space-y-2 font-mono text-xs">
                  <div className="text-[11px] font-semibold text-text-primary uppercase tracking-wider border-b border-mist pb-1.5">
                    Wallet Statistics
                  </div>

                  <div className="space-y-1.5 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-text-muted">Total Inflow:</span>
                      <span className="text-text-primary font-medium">4.73 BTC (~₹2.4 Cr)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Cluster Size:</span>
                      <span className="text-text-primary">12 wallets</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Mixer Usage:</span>
                      <span className="text-threat">Detected (Wasabi)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Chain Hop:</span>
                      <span className="text-signal">BTC → USDT → BNB</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Oldest Tx:</span>
                      <span className="text-text-secondary">2026-07-14</span>
                    </div>
                  </div>
                </div>

              </div>

            </div>
          </main>

          {/* RIGHT CONTEXT PANEL: 320px (Case summary for EOA-2026-0041) */}
          <aside className="w-[320px] min-w-[320px] h-[calc(100vh-48px)] bg-void border-l border-mist flex flex-col justify-between text-xs z-20 overflow-y-auto select-none">
            {/* Header */}
            <div className="p-3 border-b border-mist flex items-center justify-between bg-shadow">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-gaze" />
                <span className="font-semibold text-text-primary uppercase tracking-wider text-[11px] font-mono">
                  Case Dossier // EOA-2026-0041
                </span>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-gaze/15 text-gaze border border-gaze/30">
                ACTIVE
              </span>
            </div>

            {/* Content */}
            <div className="flex-1 p-3.5 space-y-3.5 overflow-y-auto">
              
              {/* Complainant & Loss */}
              <div className="bg-shadow border border-mist rounded-[4px] p-3 space-y-1.5">
                <div className="text-[11px] text-text-muted font-mono">COMPLAINANT:</div>
                <div className="text-[13px] font-medium text-text-primary">
                  Axis Bank Corporate (Redacted)
                </div>
                <div className="flex items-center justify-between pt-1.5 border-t border-mist/60 text-[11px] font-mono">
                  <span className="text-text-muted">REPORTED LOSS:</span>
                  <span className="text-text-primary font-semibold">₹2.4 Cr</span>
                </div>
              </div>

              {/* Module Convergence Status */}
              <div className="bg-shadow border border-mist rounded-[4px] p-3 space-y-2">
                <div className="text-[11px] font-mono text-text-muted uppercase">
                  Investigation Modules
                </div>

                <div className="space-y-1.5 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-text-secondary">VoiceGuard:</span>
                    <span className="text-safe flex items-center gap-1 text-[11px]">
                      <CheckCircle2 className="w-3 h-3" /> Complete ✓
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-text-secondary">ShadowTrace:</span>
                    <span className="text-text-muted text-[11px]">Pending</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-text-secondary">ChainEye:</span>
                    <span className="text-gaze text-[11px] font-semibold">Active</span>
                  </div>
                </div>

                {/* Convergence Note */}
                <div className="pt-2 border-t border-mist/60 text-[10px] text-text-secondary">
                  <span className="text-text-muted block font-mono text-[9px]">CONVERGENCE:</span>
                  Awaiting ShadowTrace submission for final triangulation.
                </div>
              </div>

              {/* Blockchain Anchoring Status */}
              <div className="bg-shadow border border-mist rounded-[4px] p-3 space-y-2 text-[10px] font-mono">
                <div className="flex items-center justify-between text-signal font-medium border-b border-mist/60 pb-1">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3 h-3" /> Polygon Mumbai
                  </span>
                  <span className="text-text-muted">UNANCHORED</span>
                </div>
                <div className="text-text-muted leading-relaxed">
                  Anchor locked until investigator submits evidence and supervisor gives cryptographic sign-off.
                </div>
              </div>

            </div>

            {/* Footer */}
            <div className="p-3 border-t border-mist bg-shadow">
              <Link
                href="/"
                className="text-gaze hover:underline text-xs font-mono font-medium flex items-center justify-center gap-1"
              >
                <span>View Full Case in Command Center</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          </aside>

        </div>
      </div>

      {/* Freeze Request Modal */}
      {isFreezeDraftOpen && (
        <div className="fixed inset-0 bg-abyss/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-void border border-mist rounded-[4px] p-4 space-y-3 font-sans shadow-none">
            <div className="flex items-center justify-between border-b border-mist pb-2">
              <div className="font-semibold text-text-primary text-sm font-mono flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-gaze" />
                <span>NCRP Emergency Freeze Order (Sec. 91 CrPC)</span>
              </div>
              <button
                onClick={() => setIsFreezeDraftOpen(false)}
                className="text-text-muted hover:text-text-primary font-mono text-xs"
              >
                [ESC]
              </button>
            </div>

            <div className="space-y-2 text-xs text-text-secondary font-mono bg-shadow p-3 rounded-[4px] border border-mist">
              <div>TARGET VASP: Binance Global (Cayman Islands)</div>
              <div>TARGET ADDRESS: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2</div>
              <div>IDENTIFIED SUB-ACCOUNTS: 3</div>
              <div>FREEZE AMOUNT: 4.73 BTC (~₹2,40,00,000 INR)</div>
              <div>CRITICAL DEADLINE: Sep 16, 02:00 UTC (Estimated Withdrawal Window)</div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-mist">
              <button
                onClick={() => setIsFreezeDraftOpen(false)}
                className="px-3 py-1.5 rounded-[4px] border border-mist text-text-secondary hover:text-text-primary text-xs font-mono"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  alert("Freeze Notice dispatched to VASP compliance liaison webhook.");
                  setIsFreezeDraftOpen(false);
                }}
                className="px-3 py-1.5 rounded-[4px] bg-gaze hover:bg-gaze/90 text-abyss font-semibold text-xs font-mono"
              >
                Transmit Order to Binance Liaison
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
