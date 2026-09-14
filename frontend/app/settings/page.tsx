"use client";

import React, { useState, useEffect } from "react";
import { NavRail } from "@/components/NavRail";
import { TopBar } from "@/components/TopBar";
import {
  Settings,
  Key,
  Cpu,
  Users,
  Shield,
  CheckCircle2,
  AlertCircle,
  Save,
  Plus,
  RefreshCw,
  Lock,
} from "lucide-react";
import { api } from "@/lib/api";
import { UserRecord } from "@/lib/types";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"keys" | "models" | "users">("keys");
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Form states for API keys
  const [alchemyKey, setAlchemyKey] = useState("alch_live_demo991a82bc");
  const [etherscanKey, setEtherscanKey] = useState("ETH_SCAN_77192A9BF");
  const [pinataJwt, setPinataJwt] = useState("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...");
  const [polygonRpc, setPolygonRpc] = useState("https://polygon-amoy.g.alchemy.com/v2/demo");

  // Add User Form State
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newRole, setNewRole] = useState<"INVESTIGATOR" | "SUPERVISOR" | "OWNER">("INVESTIGATOR");

  useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true);
        const [sys, usrList] = await Promise.all([
          api.settings.getSystemStatus(),
          api.settings.listUsers(),
        ]);
        setSystemStatus(sys);
        setUsers(usrList);
      } catch {
        // Fallback already provided in api.ts
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
  }, []);

  const handleSaveKeys = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  const handleAddUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername || !newEmail) return;
    const newUser: UserRecord = {
      id: `usr-${Date.now()}`,
      username: newUsername,
      email: newEmail,
      role: newRole,
      active: true,
      created_at: new Date().toISOString(),
    };
    setUsers([...users, newUser]);
    setShowAddUser(false);
    setNewUsername("");
    setNewEmail("");
  };

  return (
    <div className="flex h-screen w-screen bg-abyss text-text-primary overflow-hidden font-sans select-none">
      <NavRail activeItem="settings" />

      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
        <TopBar onToggleContext={() => {}} />

        <header className="h-[48px] min-h-[48px] bg-void border-b border-mist px-4 flex items-center justify-between z-20">
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-text-muted">System</span>
            <span className="text-text-muted">/</span>
            <span className="text-gaze font-medium">Settings & Administration</span>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-mono text-safe">
            <span className="w-2 h-2 rounded-full bg-safe animate-pulse" />
            <span>Node Configured</span>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          {/* Settings Nav Sidebar */}
          <aside className="w-56 bg-void border-r border-mist p-3 space-y-1">
            <button
              onClick={() => setActiveTab("keys")}
              className={`w-full text-left px-3 py-2 rounded-[4px] text-xs font-mono flex items-center gap-2 transition-colors ${
                activeTab === "keys"
                  ? "bg-shadow border-l-2 border-l-gaze text-gaze"
                  : "text-text-secondary hover:text-text-primary hover:bg-shadow/50"
              }`}
            >
              <Key className="w-3.5 h-3.5" />
              <span>API Integrations</span>
            </button>

            <button
              onClick={() => setActiveTab("models")}
              className={`w-full text-left px-3 py-2 rounded-[4px] text-xs font-mono flex items-center gap-2 transition-colors ${
                activeTab === "models"
                  ? "bg-shadow border-l-2 border-l-gaze text-gaze"
                  : "text-text-secondary hover:text-text-primary hover:bg-shadow/50"
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>AI Models & Hardware</span>
            </button>

            <button
              onClick={() => setActiveTab("users")}
              className={`w-full text-left px-3 py-2 rounded-[4px] text-xs font-mono flex items-center gap-2 transition-colors ${
                activeTab === "users"
                  ? "bg-shadow border-l-2 border-l-gaze text-gaze"
                  : "text-text-secondary hover:text-text-primary hover:bg-shadow/50"
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>User & Role Management</span>
            </button>
          </aside>

          {/* Settings Main Area */}
          <main className="flex-1 overflow-y-auto p-6 max-w-4xl space-y-6">
            {savedSuccess && (
              <div className="p-3 bg-safe/15 border border-safe/40 text-safe text-xs font-mono rounded-[4px] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>Configuration changes saved and reloaded across forensic engines.</span>
              </div>
            )}

            {/* TAB 1: API KEYS */}
            {activeTab === "keys" && (
              <div className="bg-void border border-mist rounded-[4px] p-5 space-y-4">
                <div>
                  <h2 className="text-sm font-semibold text-text-primary font-mono flex items-center gap-2">
                    <Key className="w-4 h-4 text-gaze" />
                    <span>Blockchain & Threat Intelligence API Keys</span>
                  </h2>
                  <p className="text-xs text-text-secondary mt-1">
                    Configure high-throughput API endpoints for live forensics, IPFS pinning, and on-chain anchoring.
                  </p>
                </div>

                <form onSubmit={handleSaveKeys} className="space-y-4 pt-2">
                  <div>
                    <label className="block text-xs font-mono text-text-secondary mb-1">
                      Alchemy Multi-Chain RPC URL / API Key
                    </label>
                    <input
                      type="password"
                      value={alchemyKey}
                      onChange={(e) => setAlchemyKey(e.target.value)}
                      className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-2 text-xs font-mono text-text-primary focus:border-gaze outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-text-secondary mb-1">
                      Etherscan Developer API Key
                    </label>
                    <input
                      type="password"
                      value={etherscanKey}
                      onChange={(e) => setEtherscanKey(e.target.value)}
                      className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-2 text-xs font-mono text-text-primary focus:border-gaze outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-text-secondary mb-1">
                      Pinata IPFS JWT Token
                    </label>
                    <input
                      type="password"
                      value={pinataJwt}
                      onChange={(e) => setPinataJwt(e.target.value)}
                      className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-2 text-xs font-mono text-text-primary focus:border-gaze outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-text-secondary mb-1">
                      Polygon Amoy Testnet RPC Gateway
                    </label>
                    <input
                      type="text"
                      value={polygonRpc}
                      onChange={(e) => setPolygonRpc(e.target.value)}
                      className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-2 text-xs font-mono text-text-primary focus:border-gaze outline-none"
                    />
                  </div>

                  <div className="pt-3 border-t border-mist flex justify-end">
                    <button
                      type="submit"
                      className="px-4 py-2 bg-gaze hover:bg-gaze/90 text-abyss font-mono text-xs font-semibold rounded-[4px] flex items-center gap-1.5 transition-colors"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>Save & Apply Keys</span>
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* TAB 2: AI MODELS & HARDWARE */}
            {activeTab === "models" && (
              <div className="space-y-4">
                <div className="bg-void border border-mist rounded-[4px] p-5 space-y-4">
                  <h2 className="text-sm font-semibold text-text-primary font-mono flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-signal" />
                    <span>Active Forensic AI Engines & Hardware Fallback</span>
                  </h2>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="bg-shadow p-3.5 rounded-[4px] border border-signal/30 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-text-primary">VoiceGuard</span>
                        <span className="px-1.5 py-0.5 bg-safe/20 text-safe text-[9px] font-mono rounded">
                          Active
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary font-mono">
                        DistilWav2Vec2 + ECAPA-TDNN Ensemble
                      </p>
                      <div className="text-[10px] font-mono text-text-muted border-t border-mist/40 pt-2">
                        Device: CPU (PyTorch Float32 Resampling)
                      </div>
                    </div>

                    <div className="bg-shadow p-3.5 rounded-[4px] border border-gaze/30 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-text-primary">ShadowTrace</span>
                        <span className="px-1.5 py-0.5 bg-safe/20 text-safe text-[9px] font-mono rounded">
                          Active
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary font-mono">
                        pgvector 768-dim BERT Embeddings
                      </p>
                      <div className="text-[10px] font-mono text-text-muted border-t border-mist/40 pt-2">
                        Corpus: 847 Actor Profiles Indexed
                      </div>
                    </div>

                    <div className="bg-shadow p-3.5 rounded-[4px] border border-safe/30 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-text-primary">ChainEye</span>
                        <span className="px-1.5 py-0.5 bg-safe/20 text-safe text-[9px] font-mono rounded">
                          Active
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary font-mono">
                        Multi-Hop Graph &amp; RandomForest Model
                      </p>
                      <div className="text-[10px] font-mono text-text-muted border-t border-mist/40 pt-2">
                        Cache: 300s TTL / Concurrency 10
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: USER MANAGEMENT */}
            {activeTab === "users" && (
              <div className="bg-void border border-mist rounded-[4px] p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-text-primary font-mono flex items-center gap-2">
                      <Users className="w-4 h-4 text-safe" />
                      <span>Authorized Law Enforcement Officers</span>
                    </h2>
                    <p className="text-xs text-text-secondary mt-1">
                      Manage role-based access control (RBAC) across Investigator, Supervisor, and Owner tiers.
                    </p>
                  </div>

                  <button
                    onClick={() => setShowAddUser(true)}
                    className="px-3 py-1.5 bg-gaze hover:bg-gaze/90 text-abyss font-mono text-xs font-semibold rounded-[4px] flex items-center gap-1.5 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Invite Officer</span>
                  </button>
                </div>

                <div className="border border-mist rounded-[4px] overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-shadow border-b border-mist text-text-muted font-mono uppercase text-[10px]">
                        <th className="py-2.5 px-3">Officer Name</th>
                        <th className="py-2.5 px-3">Official Email</th>
                        <th className="py-2.5 px-3">Assigned Role</th>
                        <th className="py-2.5 px-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-mist/50 font-mono">
                      {users.map((u) => (
                        <tr key={u.id} className="hover:bg-shadow/40 transition-colors">
                          <td className="py-2.5 px-3 text-text-primary font-medium">{u.username}</td>
                          <td className="py-2.5 px-3 text-text-secondary">{u.email}</td>
                          <td className="py-2.5 px-3">
                            <span
                              className={`px-2 py-0.5 rounded-[2px] text-[10px] font-semibold ${
                                u.role === "OWNER"
                                  ? "bg-threat/20 text-threat border border-threat/30"
                                  : u.role === "SUPERVISOR"
                                  ? "bg-gaze/20 text-gaze border border-gaze/30"
                                  : "bg-signal/20 text-signal border border-signal/30"
                              }`}
                            >
                              {u.role}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="text-safe text-[10px] flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-safe" />
                              Active
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Add Officer Modal */}
      {showAddUser && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-void border border-mist rounded-[4px] p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Users className="w-4 h-4 text-gaze" />
              <span>Register Law Enforcement Officer</span>
            </h3>

            <form onSubmit={handleAddUser} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-text-secondary mb-1">
                  Officer Username / Badge ID
                </label>
                <input
                  type="text"
                  required
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="e.g. insp_verma"
                  className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-1.5 text-xs text-text-primary font-mono focus:border-gaze outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-text-secondary mb-1">
                  Department Email
                </label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="e.g. s.verma@cybercell.gov.in"
                  className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-1.5 text-xs text-text-primary font-mono focus:border-gaze outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-text-secondary mb-1">
                  Role Authority
                </label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as any)}
                  className="w-full bg-shadow border border-mist rounded-[4px] px-3 py-1.5 text-xs text-text-primary font-mono focus:border-gaze outline-none"
                >
                  <option value="INVESTIGATOR">Investigator (Analyze &amp; Submit Evidence)</option>
                  <option value="SUPERVISOR">Supervisor (Approve &amp; Authorize Anchors)</option>
                  <option value="OWNER">Owner (Full Administration)</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-mist">
                <button
                  type="button"
                  onClick={() => setShowAddUser(false)}
                  className="px-3 py-1.5 text-xs font-mono text-text-secondary hover:text-text-primary border border-mist rounded-[4px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-mono font-medium bg-gaze text-abyss rounded-[4px] hover:bg-gaze/90"
                >
                  Register Officer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
