/**
 * Auth token helpers for Eye of Abyss frontend.
 * Access token → sessionStorage (cleared on tab close).
 * Refresh token → httpOnly cookie managed by case-engine.
 */

const CASE_ENGINE = process.env.NEXT_PUBLIC_CASE_ENGINE_URL ?? "http://localhost:8000";
const KEY = "eoa_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(KEY);
}

export function setToken(token: string): void {
  sessionStorage.setItem(KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

/** Fetch with automatic JWT header + one silent refresh on 401. */
export async function fetchWithAuth(url: string, opts: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers = new Headers(opts.headers ?? {});
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res = await fetch(url, { ...opts, headers, credentials: "include" });

  if (res.status === 401) {
    // Try refresh
    const refreshed = await fetch(`${CASE_ENGINE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (refreshed.ok) {
      const data = await refreshed.json();
      setToken(data.access_token);
      headers.set("Authorization", `Bearer ${data.access_token}`);
      res = await fetch(url, { ...opts, headers, credentials: "include" });
    } else {
      clearToken();
    }
  }

  return res;
}

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${CASE_ENGINE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    credentials: "include",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Login failed");
  }
  const data = await res.json();
  setToken(data.access_token);
}

export async function register(email: string, password: string, role = "VIEWER"): Promise<void> {
  const res = await fetch(`${CASE_ENGINE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, role }),
    credentials: "include",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Registration failed");
  }
  const data = await res.json();
  setToken(data.access_token);
}

export async function logout(): Promise<void> {
  await fetch(`${CASE_ENGINE}/auth/logout`, { method: "POST", credentials: "include" });
  clearToken();
}

/** Decode the JWT payload (no verify — server already did that). */
export function decodePayload(): { sub: string; role: string; email: string } | null {
  const token = getToken();
  if (!token) return null;
  try {
    const part = token.split(".")[1];
    return JSON.parse(atob(part.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}
