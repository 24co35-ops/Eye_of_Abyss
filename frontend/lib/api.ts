// ponytail: minimal typed fetch wrappers — expand per module as needed

const CASE_ENGINE = process.env.NEXT_PUBLIC_CASE_ENGINE_URL ?? "http://localhost:8000";
const VOICEGUARD  = process.env.NEXT_PUBLIC_VOICEGUARD_URL  ?? "http://localhost:8001";
const SHADOWTRACE = process.env.NEXT_PUBLIC_SHADOWTRACE_URL ?? "http://localhost:8002";
const CHAINEYE    = process.env.NEXT_PUBLIC_CHAINEYE_URL    ?? "http://localhost:8003";

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const health = {
  caseEngine:  () => get(`${CASE_ENGINE}/health`),
  voiceguard:  () => get(`${VOICEGUARD}/health`),
  shadowtrace: () => get(`${SHADOWTRACE}/health`),
  chaineye:    () => get(`${CHAINEYE}/health`),
};

export const cases = {
  list:   ()         => get(`${CASE_ENGINE}/cases`),
  get:    (id: string) => get(`${CASE_ENGINE}/cases/${id}`),
};
