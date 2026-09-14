"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  Mic,
  Fingerprint,
  Network,
  ShieldCheck,
  Settings,
  Eye,
} from "lucide-react";

export type NavItem = "dashboard" | "cases" | "voiceguard" | "shadowtrace" | "chaineye" | "anchors" | "settings";

interface NavRailProps {
  activeItem?: NavItem;
  onSelect?: (item: NavItem) => void;
}

export function NavRail({ activeItem, onSelect }: NavRailProps) {
  const pathname = usePathname();
  const router = useRouter();

  const navItems: { id: NavItem; label: string; href: string; icon: React.ReactNode }[] = [
    { id: "dashboard", label: "Command Center", href: "/", icon: <LayoutDashboard className="w-5 h-5" /> },
    { id: "cases", label: "Case Files", href: "/cases", icon: <FolderKanban className="w-5 h-5" /> },
    { id: "voiceguard", label: "VoiceGuard Audio", href: "/voiceguard", icon: <Mic className="w-5 h-5" /> },
    { id: "shadowtrace", label: "ShadowTrace Darknet", href: "/shadowtrace", icon: <Fingerprint className="w-5 h-5" /> },
    { id: "chaineye", label: "ChainEye Crypto", href: "/chaineye", icon: <Network className="w-5 h-5" /> },
    { id: "anchors", label: "Blockchain Registry", href: "/", icon: <ShieldCheck className="w-5 h-5" /> },
  ];

  const handleClick = (item: (typeof navItems)[0]) => {
    if (onSelect) onSelect(item.id);
    if (item.href !== pathname) {
      router.push(item.href);
    }
  };

  return (
    <aside className="w-[56px] min-w-[56px] h-screen bg-void border-r border-mist flex flex-col justify-between items-center py-3 z-30 select-none">
      {/* Brand Eye Icon */}
      <div className="flex flex-col items-center gap-4">
        <Link
          href="/"
          className="w-10 h-10 rounded-[4px] bg-shadow border border-mist flex items-center justify-center text-gaze hover:border-gaze transition-colors"
          title="Eye of Abyss — Command Center"
        >
          <Eye className="w-5 h-5" />
        </Link>

        {/* Navigation Items */}
        <nav className="flex flex-col gap-1.5 mt-2">
          {navItems.map((item) => {
            const isActive = activeItem
              ? activeItem === item.id
              : item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

            return (
              <button
                key={item.id}
                onClick={() => handleClick(item)}
                title={item.label}
                className={`group relative w-10 h-10 rounded-[4px] flex items-center justify-center transition-all ${
                  isActive
                    ? "bg-shadow text-gaze border-l-2 border-l-gaze border-t border-r border-b border-mist"
                    : "text-text-secondary hover:text-text-primary hover:bg-shadow"
                }`}
              >
                {item.icon}

                {/* Micro tooltip */}
                <span className="absolute left-[58px] px-2 py-1 bg-shadow border border-mist text-text-primary text-[11px] font-medium rounded-[4px] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity z-50 shadow-none">
                  {item.label}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Settings & Status */}
      <div className="flex flex-col items-center gap-2">
        <button
          onClick={() => {
            if (onSelect) onSelect("settings");
            if (pathname !== "/settings") router.push("/settings");
          }}
          title="System Settings"
          className={`w-10 h-10 rounded-[4px] flex items-center justify-center transition-all ${
            pathname === "/settings" || activeItem === "settings"
              ? "bg-shadow text-gaze border border-mist"
              : "text-text-muted hover:text-text-secondary hover:bg-shadow"
          }`}
        >
          <Settings className="w-4 h-4" />
        </button>

        {/* Officer Avatar */}
        <div
          className="w-8 h-8 rounded-[4px] bg-shadow border border-mist flex items-center justify-center text-[10px] font-mono font-medium text-text-primary"
          title="Insp. R. Mehta (Cybercrime Cell)"
        >
          RM
        </div>
      </div>
    </aside>
  );
}
