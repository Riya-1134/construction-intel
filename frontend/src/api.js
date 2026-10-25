// Thin API client. Every call returns the parsed JSON contract or throws an ApiError
// with a human-readable message so pages can render a stable error state.
// Accepts a full URL or a bare host (Render injects hosts without a scheme).
function normaliseBase(raw) {
  const v = (raw || "").trim().replace(/\/+$/, "");
  if (!v) return "http://localhost:8000";
  return /^https?:\/\//i.test(v) ? v : `https://${v}`;
}
const BASE = normaliseBase(import.meta.env.VITE_API_BASE_URL);

export class ApiError extends Error {
  constructor(message, status, errors = []) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

async function handle(res) {
  let body = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }
  if (!res.ok) {
    const detail = body?.detail || `Request failed (${res.status})`;
    throw new ApiError(detail, res.status, Array.isArray(body?.errors) ? body.errors : []);
  }
  return body ?? {};
}

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new ApiError("Cannot reach the backend. Is the FastAPI server running on " + BASE + "?", 0);
  }
  return handle(res);
}

export function postJson(path, payload) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function postForm(path, fields) {
  const form = new FormData();
  Object.entries(fields).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    form.append(k, v);
  });
  return request(path, { method: "POST", body: form });
}

export const api = {
  health: () => request("/api/health"),
  safety: (fields) => postForm("/api/safety/analyze", fields),
  crack: (fields) => postForm("/api/crack/analyze", fields),
  planner: (body) => postJson("/api/planner/generate", body),
  valuation: (body) => postJson("/api/valuation/estimate", body),
  chat: (body) => postJson("/api/chat", body),
  daily: (body) => postJson("/api/daily/plan", body),
  weather: (body) => postJson("/api/weather/advisory", body),
};

// Safe accessors so UI never calls .map on undefined.
export const list = (v) => (Array.isArray(v) ? v : []);
export const num = (v) => (typeof v === "number" && Number.isFinite(v) ? v : 0);
export const inr = (v) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(num(v));
export const compactInr = (v) => {
  const n = num(v);
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return inr(n);
};
