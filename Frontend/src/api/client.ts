const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type AnalyzeRequest = { email: string };

export type EvidenceItem = {
  source: string;
  snippet: string;
  url?: string | null;
};

export type AnalyzeResponse = {
  input_email: string;
  person_name_guess?: string | null;
  company_domain?: string | null;
  confidence: { label: "low" | "medium" | "high"; rationale: string };
  study_of_person: {
    likely_role_focus?: string | null;
    domain?: string | null;
    communication_style?: string | null;
  };
  recommendations: {
    dress?: string | null;
    tone?: string | null;
    dos: string[];
    donts: string[];
    connecting_points: string[];
    suggested_agenda: string[];
  };
  evidence: EvidenceItem[];
};

export async function analyze(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE_URL}/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }

  return (await res.json()) as AnalyzeResponse;
}
