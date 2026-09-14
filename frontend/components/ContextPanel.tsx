"use client";

import React from "react";
import {
  X,
  ExternalLink,
  ShieldCheck,
  FileText,
  Layers,
  Fingerprint,
  Mic,
  Network,
  CheckCircle2,
} from "lucide-react";
import { CaseRecord } from "@/lib/types";

interface ContextPanelProps {
  isOpen: boolean;
  onClose: () => void;
  caseData?: CaseRecord | null;
}

export function ContextPanel({ isOpen, onClose, caseData }: ContextPanelProps) {
  if (!isOpen || !caseData) return null;

  return (
    <aside className="w-[320px] min-w-[320px] h-[calc(100vh-48px)] bg-void border-l border-mist flex flex-col justify-between text-xs z-20 overflow-y-auto animate-in slide-in-from-right duration-150 select-none">
      {/* Panel Header */}
      <div className="p-3 border-b border-mist flex items-center justify-between bg-shadow">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-gaze" />
          <span className="font-semibold text-text-primary uppercase tracking-wider text-[11px] font-mono">
            Case Context // {caseData.caseId}
          </span>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 rounded-[4px] border border-mist bg-void flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-text-secondary transition-colors"
          title="Close panel"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Dossier Content */}
      <div className="flex-1 p-3 space-y-3.5 overflow-y-auto">
        {/* Case ID & Threat Level */}
        <div className="bg-shadow border border-mist rounded-[4px] p-2.5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-gaze font-semibold text-sm">
              {caseData.caseId}
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
                caseData.status === "ANCHORED"
                  ? "bg-signal/15 text-signal border border-signal/30"
                  : caseData.status === "ACTIVE"
                  ? "bg-gaze/15 text-gaze border border-gaze/30"
                  : caseData.status === "FILED"
                  ? "bg-safe/15 text-safe border border-safe/30"
                  : "bg-void text-text-muted border border-mist"
              }`}
            >
              {caseData.status}
            </span>
          </div>

          <div className="text-[12px] text-text-primary font-medium leading-snug">
            {caseData.complainant}
          </div>
          {caseData.reportedLoss && (
            <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-mist/60 font-mono">
              <span className="text-text-muted">REPORTED LOSS:</span>
              <span className="text-text-primary font-medium">{caseData.reportedLoss}</span>
            </div>
          )}
        </div>

        {/* Cross-Module Convergence Score */}
        <div className="bg-shadow border border-mist rounded-[4px] p-2.5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-text-muted uppercase text-[10px] font-mono tracking-wider">
              Cross-Module Signals
            </span>
            <span className="font-mono text-gaze font-bold text-xs">
              {((caseData.convergenceScore || 0.88) * 100).toFixed(0)}% Match
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-1.5 bg-void rounded-none overflow-hidden flex">
            <div
              className="h-full bg-gaze"
              style={{ width: `${(caseData.convergenceScore || 0.88) * 100}%` }}
            />
          </div>

          {/* Module Signal Chips */}
          <div className="space-y-1.5 pt-1 text-[11px]">
            {caseData.modules.includes("VG") && (
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-secondary">
                  <Mic className="w-3 h-3 text-signal" /> VoiceGuard:
                </span>
                <span className="font-mono text-text-primary text-[10px] truncate max-w-[140px]">
                  {caseData.voiceVerdict || "Synthetic (0.94)"}
                </span>
              </div>
            )}

            {caseData.modules.includes("ST") && (
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-secondary">
                  <Fingerprint className="w-3 h-3 text-gaze" /> ShadowTrace:
                </span>
                <span className="font-mono text-text-primary text-[10px] truncate max-w-[140px]">
                  {caseData.actorHandle || "@phantom_trade"}
                </span>
              </div>
            )}

            {caseData.modules.includes("CE") && (
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-text-secondary">
                  <Network className="w-3 h-3 text-safe" /> ChainEye:
                </span>
                <span className="font-mono text-text-primary text-[10px] truncate max-w-[140px]">
                  {caseData.walletTarget || "0x71C...498B"}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Blockchain Anchoring & Chain of Custody */}
        <div className="bg-shadow border border-mist rounded-[4px] p-2.5 space-y-2">
          <div className="flex items-center justify-between border-b border-mist/60 pb-1.5">
            <div className="flex items-center gap-1.5 text-signal font-medium text-[11px]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Polygon Amoy Anchor</span>
            </div>
            {caseData.status === "ANCHORED" || caseData.status === "FILED" ? (
              <span className="text-safe text-[10px] font-mono flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> VERIFIED
              </span>
            ) : (
              <span className="text-text-muted text-[10px] font-mono">
                PENDING APPROVAL
              </span>
            )}
          </div>

          <div className="space-y-1.5 text-[10px] font-mono">
            <div>
              <span className="text-text-muted block text-[9px]">TX HASH:</span>
              <span className="text-signal break-all block leading-tight pt-0.5">
                {caseData.txHash || "Pending transaction"}
              </span>
            </div>

            <div>
              <span className="text-text-muted block text-[9px]">IPFS CID (PINATA):</span>
              <span className="text-text-secondary break-all block leading-tight pt-0.5">
                {caseData.ipfsCid || "Pending IPFS pin"}
              </span>
            </div>

            <div>
              <span className="text-text-muted block text-[9px]">SHA-256 INTEGRITY DIGEST:</span>
              <span className="text-text-secondary break-all block leading-tight pt-0.5">
                {caseData.evidenceHash || "Computed on submission"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Panel Footer Actions */}
      <div className="p-3 border-t border-mist bg-shadow space-y-2">
        <button className="w-full py-2 bg-gaze hover:bg-gaze/90 text-abyss font-semibold rounded-[4px] text-xs transition-colors flex items-center justify-center gap-1.5">
          <FileText className="w-3.5 h-3.5" />
          <span>Export Evidence Dossier (PDF)</span>
        </button>

        <button className="w-full py-1.5 bg-void hover:bg-shadow text-text-primary border border-mist rounded-[4px] text-xs font-mono transition-colors flex items-center justify-center gap-1.5">
          <ExternalLink className="w-3 h-3 text-signal" />
          <span>Verify On PolygonScan</span>
        </button>
      </div>
    </aside>
  );
}
