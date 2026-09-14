"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Menu,
  Bell,
  AlertTriangle,
  FileText,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  X,
} from "lucide-react";

export default function MobileWithdrawalAlertPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [freezeDrafted, setFreezeDrafted] = useState(false);

  return (
    <div className="min-h-screen bg-[#0D0B14] flex items-center justify-center p-0 md:p-6 text-[#E8E6F2]">
      {/* 390px Mobile Viewport Container */}
      <div className="w-full max-w-[390px] min-h-screen md:min-h-[844px] md:h-[844px] bg-[#0D0B14] md:border md:border-[#2A2640] md:rounded-[4px] flex flex-col overflow-hidden relative">
        
        {/* Slide-out Menu Drawer */}
        {menuOpen && (
          <div className="absolute inset-0 bg-[#0D0B14]/98 z-50 p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-[#2A2640]">
                <span className="font-semibold text-base text-[#F0A500]">Eye of Abyss</span>
                <button
                  onClick={() => setMenuOpen(false)}
                  className="p-1 text-[#8884A8] hover:text-[#E8E6F2]"
                  aria-label="Close menu"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="flex flex-col gap-2 mt-6">
                {[
                  { label: "Command Center", href: "/" },
                  { label: "Case Files", href: "/cases" },
                  { label: "VoiceGuard Audio", href: "/voiceguard" },
                  { label: "ShadowTrace Darknet", href: "/shadowtrace" },
                  { label: "ChainEye Crypto", href: "/chaineye" },
                ].map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMenuOpen(false)}
                    className="flex items-center justify-between px-3 py-2.5 rounded-[4px] bg-[#13111E] border border-[#2A2640] text-sm text-[#E8E6F2] hover:border-[#F0A500] transition-colors"
                  >
                    <span>{item.label}</span>
                    <ChevronRight className="w-4 h-4 text-[#8884A8]" />
                  </Link>
                ))}
              </nav>
            </div>

            <div className="text-[11px] text-[#4A4768] font-mono text-center">
              Insp. R. Mehta · Law Enforcement Cell
            </div>
          </div>
        )}

        {/* Top Bar (Prompt 6 Spec) */}
        <header className="h-12 border-b border-[#2A2640] bg-[#13111E] px-4 flex items-center justify-between shrink-0">
          <button
            onClick={() => setMenuOpen(true)}
            className="p-1 text-[#8884A8] hover:text-[#E8E6F2] focus:outline-none"
            aria-label="Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="font-semibold text-sm tracking-tight text-[#E8E6F2]">
            Eye of Abyss
          </div>

          <div className="relative">
            <Bell className="w-5 h-5 text-[#8884A8]" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#F0A500]" />
          </div>
        </header>

        {/* Full-bleed Alert Banner at Top */}
        <div className="bg-[#C92A2A] px-4 py-3 flex items-center justify-between text-white shrink-0">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center">
              {/* Amber animated pulse ring around warning icon */}
              <span className="absolute w-7 h-7 rounded-full border border-[#F0A500] animate-ping opacity-80" />
              <div className="w-6 h-6 rounded-full bg-[#F0A500]/20 flex items-center justify-center border border-[#F0A500]">
                <AlertTriangle className="w-3.5 h-3.5 text-[#F0A500]" />
              </div>
            </div>
            <div>
              <div className="font-semibold text-[14px] uppercase tracking-wide leading-tight">
                WITHDRAWAL ALERT
              </div>
              <div className="text-[12px] opacity-90 leading-tight mt-0.5 font-normal">
                EOA-2026-0041 — ChainEye
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <main className="p-4 flex-1 flex flex-col gap-4 justify-between overflow-y-auto">
          
          <div className="flex flex-col gap-4">
            {/* Alert Detail Card */}
            <div className="bg-[#1C1929] border-l-4 border-l-[#F0A500] border border-[#2A2640] rounded-[4px] p-4 flex flex-col gap-2">
              <div className="text-[12px] text-[#8884A8] font-normal">
                Predicted window opens in
              </div>
              
              <div className="font-mono font-bold text-[48px] leading-none text-[#F0A500] tracking-tight my-1">
                3h 42m
              </div>

              <div className="font-mono text-[12px] text-[#8884A8]">
                Sep 16, 02:00–04:00 UTC
              </div>

              <div className="mt-2">
                <div className="flex justify-between items-center text-[10px] mb-1">
                  <span className="text-[#8884A8]">Confidence</span>
                  <span className="font-mono text-[#6B4FFF] font-medium">74%</span>
                </div>
                <div className="w-full h-1.5 bg-[#2A2640] rounded-full">
                  <div className="h-1.5 bg-[#6B4FFF] rounded-full" style={{ width: "74%" }} />
                </div>
              </div>
            </div>

            {/* Key Data Monospace List */}
            <div className="bg-[#13111E] border border-[#2A2640] rounded-[4px] p-3.5 flex flex-col gap-2 font-mono text-xs">
              <div className="flex justify-between items-center py-0.5 border-b border-[#2A2640]/50">
                <span className="text-[#8884A8]">Wallet</span>
                <span className="text-[#E8E6F2]">1BvBMSE...VN2</span>
              </div>
              <div className="flex justify-between items-center py-0.5 border-b border-[#2A2640]/50">
                <span className="text-[#8884A8]">Amount</span>
                <span className="text-[#E8E6F2]">4.73 BTC (~₹2.4 Cr)</span>
              </div>
              <div className="flex justify-between items-center py-0.5 border-b border-[#2A2640]/50">
                <span className="text-[#8884A8]">VASP</span>
                <span className="text-[#E8E6F2]">Binance Global</span>
              </div>
              <div className="flex justify-between items-center py-0.5">
                <span className="text-[#8884A8]">Pattern</span>
                <span className="text-[#E8E6F2]">T2 dormancy cycle</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            {/* Two Action Buttons Stacked */}
            <div className="flex flex-col gap-2">
              <button
                onClick={() => setFreezeDrafted(true)}
                className={`w-full py-2.5 px-4 text-sm font-medium rounded-[4px] transition-colors flex items-center justify-center gap-2 ${
                  freezeDrafted
                    ? "bg-[#2A9D4E] text-white"
                    : "bg-[#F0A500] text-[#0D0B14] hover:bg-[#F0A500]/90"
                }`}
              >
                {freezeDrafted ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" /> Freeze Request Drafted
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" /> Draft Freeze Request
                  </>
                )}
              </button>

              <Link
                href="/chaineye"
                className="w-full py-2.5 px-4 text-sm font-medium text-center rounded-[4px] bg-[#2A2640] border border-[#2A2640] text-[#E8E6F2] hover:border-[#8884A8] transition-colors flex items-center justify-center gap-1.5"
              >
                <span>View Full Case</span>
                <ArrowRight className="w-4 h-4 text-[#8884A8]" />
              </Link>
            </div>

            {/* Bottom - Recent Module Status (Compact) */}
            <div className="pt-2 border-t border-[#2A2640] flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#2A9D4E]/10 border border-[#2A9D4E]/30 rounded-[4px] text-[#2A9D4E]">
                <CheckCircle2 className="w-3 h-3" />
                <span className="font-medium">VoiceGuard</span>
              </div>

              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#1C1929] border border-[#2A2640] rounded-[4px] text-[#8884A8]">
                <span>—</span>
                <span>ShadowTrace</span>
              </div>

              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#F0A500]/10 border border-[#F0A500]/40 rounded-[4px] text-[#F0A500]">
                <AlertTriangle className="w-3 h-3" />
                <span className="font-medium">ChainEye</span>
              </div>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
