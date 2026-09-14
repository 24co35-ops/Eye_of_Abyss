"use client";

import React from "react";
import { Bell, PanelRight, Shield, Activity, Search } from "lucide-react";

interface TopBarProps {
  onToggleContext: () => void;
  isContextOpen: boolean;
  activeCaseId?: string | null;
}

export function TopBar({ onToggleContext, isContextOpen, activeCaseId }: TopBarProps) {
  return (
    <header className="h-[48px] min-h-[48px] bg-void border-b border-mist px-4 flex items-center justify-between z-20 select-none">
      {/* Left: Brand Wordmark */}
      <div className="flex items-center gap-3">
        <span className="text-[15px] font-semibold tracking-wide text-text-primary">
          EYE OF <span className="text-gaze font-bold">ABYSS</span>
        </span>
        <span className="text-text-muted text-xs">/</span>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] bg-shadow border border-mist text-[11px] font-mono text-text-secondary">
          <span className="w-1.5 h-1.5 rounded-full bg-safe animate-pulse" />
          <span>POLYGON MUMBAI: ANCHOR LIVE</span>
        </div>
      </div>

      {/* Center: Search / Filter input */}
      <div className="hidden md:flex items-center w-72 h-7 bg-shadow border border-mist rounded-[4px] px-2.5 text-xs text-text-secondary focus-within:border-gaze">
        <Search className="w-3.5 h-3.5 text-text-muted mr-2" />
        <input
          type="text"
          placeholder="Search case ID, wallet, actor handle..."
          className="bg-transparent text-text-primary text-xs outline-none w-full placeholder:text-text-muted font-mono"
        />
      </div>

      {/* Right: Officer Profile, Alerts, Context Panel Toggle */}
      <div className="flex items-center gap-3">
        {/* Active Case Indicator */}
        {activeCaseId && (
          <div className="hidden lg:flex items-center gap-1.5 px-2 py-0.5 bg-gaze/10 border border-gaze/30 rounded-[4px] text-xs font-mono text-gaze">
            <span>ACTIVE CASE:</span>
            <span className="font-semibold">{activeCaseId}</span>
          </div>
        )}

        {/* Notifications Bell with Amber Dot */}
        <button
          className="relative w-8 h-8 rounded-[4px] bg-shadow border border-mist flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-text-secondary transition-colors"
          title="3 Unread Alerts"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-gaze border border-void" />
        </button>

        {/* Officer Info */}
        <div className="flex items-center gap-2 pl-1 border-l border-mist">
          <div className="text-right leading-tight">
            <div className="text-xs font-medium text-text-primary">Insp. R. Mehta</div>
            <div className="text-[10px] text-text-muted font-mono">CYBER CELL #04</div>
          </div>
        </div>

        {/* Right Context Panel Toggle */}
        <button
          onClick={onToggleContext}
          title={isContextOpen ? "Collapse Context Panel" : "Expand Context Panel"}
          className={`w-8 h-8 rounded-[4px] border flex items-center justify-center transition-colors ${
            isContextOpen
              ? "bg-shadow text-gaze border-gaze"
              : "bg-shadow text-text-secondary border-mist hover:text-text-primary"
          }`}
        >
          <PanelRight className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
