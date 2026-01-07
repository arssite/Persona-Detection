const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type AnalyzeRequest = { email: string };

export type EvidenceItem = {
  source: string;
  snippet: string;
  url?: string | null;
};

export type Confidence = { label: "low" | "medium" | "high"; rationale: string };

export type GitHubRepo = {
  name?: string | null;
  html_url?: string | null;
  description?: string | null;
  language?: string | null;
  stargazers_count?: number | null;
  updated_at?: string | null;
};

export type GitHubProfile = {
  username: string;
  html_url: string;
  name?: string | null;
  company?: string | null;
  location?: string | null;
  bio?: string | null;
  public_repos?: number | null;
  followers?: number | null;
  following?: number | null;
  top_languages: string[];
  top_repos: GitHubRepo[];
};

export type AnalyzeResponse = {
  input_email: string;
  person_name_guess?: string | null;
  company_domain?: string | null;

  confidence: Confidence;
  company_confidence?: Confidence | null;
  person_confidence?: Confidence | null;

  one_minute_brief?: string | null;
  questions_to_ask: string[];
  email_openers?: { formal?: string | null; warm?: string | null; technical?: string | null } | null;
  red_flags: string[];

  company_profile?: {
    summary?: string | null;
    likely_products_services: string[];
    hiring_signals: string[];
    recent_public_mentions: string[];
  } | null;

  study_of_person: {
    likely_role_focus?: string | null;
    domain?: string | null;
    communication_style?: string | null;
    seniority_signal?: string | null;
    public_presence_signal?: string | null;
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
  github_profile?: GitHubProfile | null;
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
