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


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    input_email: str
    person_name_guess: str | None = None
    company_domain: str | None = None
    confidence: Confidence
    study_of_person: StudyOfPerson
    recommendations: Recommendations
    evidence: list[EvidenceItem] = []
