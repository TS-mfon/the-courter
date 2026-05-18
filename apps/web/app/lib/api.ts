export const apiBase = "/api";

function parseErrorPayload(raw: string): { detail?: unknown } {
  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    return { detail: raw };
  }
}

function normalizeErrorMessage(status: number, raw: string): string {
  const error = parseErrorPayload(raw);
  if (typeof error.detail === "string" && error.detail.trim()) return error.detail;
  if (status >= 502) return "Backend is down. Please try again later.";
  return raw || "Request failed.";
}

export async function apiGet<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, { cache: "no-store" });
  } catch {
    throw new Error("Backend is down. Please try again later.");
  }
  if (!response.ok) {
    const raw = await response.text();
    throw new Error(normalizeErrorMessage(response.status, raw));
  }
  return response.json();
}

export async function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      method: "POST",
      headers: isForm ? undefined : { "Content-Type": "application/json", ...(init?.headers || {}) },
      body: isForm ? body : JSON.stringify(body),
      ...init
    });
  } catch {
    throw new Error("Backend is down. Please try again later.");
  }
  if (!response.ok) {
    const raw = await response.text();
    throw new Error(normalizeErrorMessage(response.status, raw));
  }
  return response.json();
}

export type ApiCase = {
  id: string;
  username: string;
  country: string;
  dispute_type: string;
  court_type: string;
  status: string;
  public: boolean;
  structured_evidence: Record<string, unknown>[];
  contradiction_report: { contradiction_detected: boolean; severity: number; issues: string[] };
  timeline: Record<string, unknown>[];
  fraud_report: { suspicious: boolean; signals: string[]; severity: number };
  retrieved_laws: { section_id?: string; title?: string; summary?: string; importance?: number; relevance?: number }[];
  judge_reasoning: {
    judge: string;
    profile: string;
    confidence: number;
    reasoning: string[];
    laws_used: string[];
    contradictions_detected: string[];
    cited_laws: { section_id: string; title: string; summary: string; relevance: number }[];
  }[];
  verdict: {
    winner: string;
    confidence: number;
    judges_used: string[];
    laws_used: string[];
    reasoning_summary: string[];
    contradictions: string[];
    headline_verdict: string;
    final_conclusion: string;
    filing_summary: string;
    evidence_overview: string;
    judge_panels: {
      judge: string;
      profile: string;
      confidence: number;
      reasoning: string[];
      laws_used: string[];
      contradictions_detected: string[];
      cited_laws: { section_id: string; title: string; summary: string; relevance: number }[];
    }[];
    law_citations: { section_id: string; title: string; summary: string; relevance: number }[];
    appealable: boolean;
    finalized: boolean;
  };
  plain_english_verdict: string;
  ocr?: { files_processed: number; degraded: boolean; methods: string[] };
  payment?: { required_fee_gen: number; court_type: string; status: string };
  appeal?: Record<string, unknown>;
};

export type Proposal = {
  id: string;
  case_id: string;
  current_verdict: string;
  status: string;
  yes_weight: number;
  no_weight: number;
  deadline: string;
  votes: { wallet: string; vote: "YES" | "NO"; weight: number; timestamp: string }[];
  final_message?: string;
};
