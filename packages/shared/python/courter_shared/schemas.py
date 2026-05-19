from pydantic import BaseModel, Field


class CaseIntake(BaseModel):
    username: str
    country: str
    dispute_type: str
    court_type: str = "public"
    claimant_statement: str
    respondent_statement: str | None = None
    workflow_type: str | None = None
    counterparty_name: str | None = None
    contract_reference: str | None = None
    claim_value_summary: str | None = None
    agreement_confirmed: bool = False


class StructuredEvidence(BaseModel):
    document_type: str
    country: str
    owner: str | None = None
    registry_id: str | None = None
    confidence: float = Field(ge=0, le=1)
    issues_detected: list[str] = Field(default_factory=list)


class ContradictionReport(BaseModel):
    contradiction_detected: bool
    severity: float = Field(ge=0, le=1)
    issues: list[str] = Field(default_factory=list)


class LawCitation(BaseModel):
    section_id: str
    title: str
    summary: str
    relevance: float = Field(default=0.5, ge=0, le=1)


class JudgePanel(BaseModel):
    judge: str
    profile: str
    confidence: float = Field(ge=0, le=1)
    reasoning: list[str] = Field(default_factory=list)
    laws_used: list[str] = Field(default_factory=list)
    cited_laws: list[LawCitation] = Field(default_factory=list)
    contradictions_detected: list[str] = Field(default_factory=list)


class Verdict(BaseModel):
    winner: str
    confidence: float = Field(ge=0, le=1)
    judges_used: list[str]
    laws_used: list[str]
    reasoning_summary: list[str]
    contradictions: list[str]
    headline_verdict: str = ""
    final_conclusion: str = ""
    filing_summary: str = ""
    evidence_overview: str = ""
    judge_panels: list[JudgePanel] = Field(default_factory=list)
    law_citations: list[LawCitation] = Field(default_factory=list)
    appealable: bool = True
    finalized: bool = True
