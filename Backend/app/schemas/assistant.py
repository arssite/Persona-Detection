from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.meeting_intel import AnalyzeResponse, EvidenceItem


class AssistantAgenda(BaseModel):
    """User-provided context about what they are trying to pitch/sell and the meeting context."""

    model_config = ConfigDict(extra="ignore")

    pitch: str = Field(..., description="What the user is pitching/selling/offering")
    goal: str = Field(..., description="Desired outcome (e.g., book next meeting, close deal, align requirements)")
    meeting_type: str | None = Field(
        default=None,
        description="Intro call | technical deep dive | discovery | negotiation | other",
    )
    audience_context: str | None = Field(
        default=None,
        description="Anything the user knows about the audience / stakeholders",
    )
    constraints: str | None = Field(
        default=None,
        description="Constraints like budget, timeline, compliance, pricing boundaries",
    )


class AssistantBootstrapRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str
    agenda: AssistantAgenda
    # If true, bypass short TTL caches and re-collect public signals.
    refresh_public_signals: bool = False


class AssistantBootstrapResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: str
    assistant_name: str = "Mr Assistant"

    # A short message that sets expectations.
    intro: str

    # Explicit: requested feature.
    starter_questions: list[str] = []

    # Pitch help
    pitch_openers: list[str] = []
    pitch_structure: list[str] = []
    likely_objections: list[str] = []
    objection_responses: list[str] = []

    # Grounding
    confidence: str = "medium"  # low|medium|high (string for simplicity)
    citations: list[EvidenceItem] = []

    # Helpful context for UI (optional)
    analyze_snapshot: AnalyzeResponse


class AssistantChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: str
    message: str

    # If the backend recommends a refresh, the UI should ask the user and then re-send the same message with confirm_refresh=True
    confirm_refresh: bool = False


class AssistantChatResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: str
    assistant_name: str = "Mr Assistant"

    message: str
    follow_up_questions: list[str] = []

    refresh_recommended: bool = False
    refresh_reason: str | None = None

    citations: list[EvidenceItem] = []
