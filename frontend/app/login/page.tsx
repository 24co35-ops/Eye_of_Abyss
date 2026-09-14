"use client";

import { useState, FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const from = params.get("from") ?? "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push(from);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleWallet() {
    if (!window.ethereum) {
      setError("MetaMask not installed");
      return;
    }
    setLoading(true);
    try {
      const [address] = await window.ethereum.request({ method: "eth_requestAccounts" });
      const message = `Eye of Abyss login: ${Date.now()}`;
      const signature = await window.ethereum.request({
        method: "personal_sign",
        params: [message, address],
      });
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_CASE_ENGINE_URL}/auth/wallet-login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ wallet_address: address, message, signature }),
          credentials: "include",
        }
      );
      if (!res.ok) throw new Error((await res.json()).detail ?? "Wallet login failed");
      const { access_token } = await res.json();
      sessionStorage.setItem("eoa_access_token", access_token);
      router.push(from);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Wallet login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0a0a1a] via-[#0d1a2e] to-[#0a0a1a]">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center text-xl">
              👁
            </div>
            <span className="text-2xl font-bold text-white tracking-tight">Eye of Abyss</span>
          </div>
          <p className="text-slate-400 text-sm">Investigation Intelligence Platform</p>
        </div>

        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          <h1 className="text-xl font-semibold text-white mb-6">Sign in to your account</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Email</label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@cyberpolice.gov.in"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Password</label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white placeholder-slate-600 text-sm focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition"
              />
            </div>

            {error && (
              <p className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-medium py-2.5 rounded-lg text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>

          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-transparent text-slate-500">or</span>
            </div>
          </div>

          <button
            id="wallet-login"
            onClick={handleWallet}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium py-2.5 rounded-lg text-sm transition-all disabled:opacity-50"
          >
            <span>🦊</span> Connect MetaMask
          </button>

          <p className="text-center text-xs text-slate-500 mt-6">
            No account?{" "}
            <a href="/register" className="text-violet-400 hover:text-violet-300 transition">
              Register
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
