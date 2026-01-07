from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: str = Field(..., examples=["firstname.lastname@company.com"])


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: str = Field(..., description="Where the signal came from (search/company_site/etc)")
    snippet: str
    url: str | None = None


class StudyOfPerson(BaseModel):
    model_config = ConfigDict(extra="ignore")
    likely_role_focus: str | None = None
    domain: str | None = None
    communication_style: str | None = None
    seniority_signal: str | None = None
    public_presence_signal: str | None = None


class Recommendations(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dress: str | None = None
    tone: str | None = None
    dos: list[str] = []
    donts: list[str] = []
    connecting_points: list[str] = []
    suggested_agenda: list[str] = []


class Confidence(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: str = Field(..., description="low|medium|high")
    rationale: str


class GitHubRepo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str | None = None
    html_url: str | None = None
    description: str | None = None
    language: str | None = None
    stargazers_count: int | None = None
    updated_at: str | None = None


class GitHubProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    username: str
    html_url: str
    name: str | None = None
    company: str | None = None
    location: str | None = None
    bio: str | None = None
    public_repos: int | None = None
    followers: int | None = None
    following: int | None = None
    top_languages: list[str] = []
    top_repos: list[GitHubRepo] = []


class EmailOpeners(BaseModel):
    model_config = ConfigDict(extra="ignore")
    formal: str | None = None
    warm: str | None = None
    technical: str | None = None


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: str | None = None
    likely_products_services: list[str] = []
    hiring_signals: list[str] = []
    recent_public_mentions: list[str] = []


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    input_email: str
    person_name_guess: str | None = None
    company_domain: str | None = None

    # Overall confidence (existing)
    confidence: Confidence

    # Split confidence (new; optional)
    company_confidence: Confidence | None = None
    person_confidence: Confidence | None = None

    one_minute_brief: str | None = None
    questions_to_ask: list[str] = []
    email_openers: EmailOpeners | None = None
    red_flags: list[str] = []

    company_profile: CompanyProfile | None = None

    study_of_person: StudyOfPerson
    recommendations: Recommendations
    evidence: list[EvidenceItem] = []

    # Optional public enrichment
    github_profile: GitHubProfile | None = None
