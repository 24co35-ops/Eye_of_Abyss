"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { clearToken, decodePayload, isLoggedIn, logout } from "@/lib/auth";

const NO_NAV = ["/login", "/register"];

export default function NavBar() {
  const pathname = usePathname();
  const router   = useRouter();
  const [user, setUser]       = useState<{ email: string; role: string } | null>(null);
  const [loggingOut, setOut]  = useState(false);

  useEffect(() => {
    const p = decodePayload();
    setUser(p ? { email: p.email, role: p.role } : null);
  }, [pathname]);

  if (NO_NAV.includes(pathname)) return null;
  if (!isLoggedIn()) return null;

  async function handleLogout() {
    setOut(true);
    await logout();
    router.push("/login");
  }

  return (
    <header className="fixed top-0 inset-x-0 z-50 h-14 flex items-center justify-between px-6 border-b border-white/10 bg-[#0a0a1a]/80 backdrop-blur-md">
      <a href="/" className="flex items-center gap-2 text-white font-semibold text-sm">
        <span className="text-lg">👁</span> Eye of Abyss
      </a>

      {user && (
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-400 hidden sm:block">
            <span className="text-violet-400 font-medium">{user.role}</span>
            {" · "}{user.email}
          </span>
          <button
            id="logout-btn"
            onClick={handleLogout}
            disabled={loggingOut}
            className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-slate-300 hover:bg-white/10 hover:text-white transition disabled:opacity-50"
          >
            {loggingOut ? "…" : "Sign out"}
          </button>
        </div>
      )}
    </header>
  );
}
