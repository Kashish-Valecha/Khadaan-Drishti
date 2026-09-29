from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RiskBand = Literal["Low", "Medium", "High"]
MineType = Literal["open-cast", "underground"]
AlertStatus = Literal["open", "reviewed", "action_taken"]


class ChecklistItem(BaseModel):
    clause: str
    found: bool
    confidence: float = Field(ge=0, le=1)
    category: Literal["safety", "environmental", "labor"]
    evidence: str | None = None


class MineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mine_id: str
    name: str
    state: str
    district: str
    type: MineType
    operator: str


class MineCreate(BaseModel):
    """A field-created record. The starting score is an inspector assessment, not a legal finding."""

    name: str = Field(min_length=3, max_length=180)
    state: str = Field(min_length=2, max_length=80)
    district: str = Field(min_length=2, max_length=100)
    type: MineType
    operator: str = Field(min_length=2, max_length=160)
    initial_score: float = Field(default=80, ge=0, le=100)
    created_by: str = Field(default="Inspector", min_length=2, max_length=100)


class ComplianceScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mine_id: str
    safety_score: float
    environmental_score: float
    labor_score: float
    composite_score: float
    risk_band: RiskBand
    last_updated: datetime


class MineListItem(MineRead):
    score: ComplianceScoreRead


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mine_id: str
    document_type: str
    upload_date: datetime
    checklist_results: list[ChecklistItem]
    overall_document_status: str
    source_filename: str | None = None
    extracted_text_preview: str | None = None


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mine_id: str
    event_type: str
    severity: Literal["Low", "Medium", "High"]
    timestamp: datetime
    status: AlertStatus
    description: str
    assigned_to: str | None = None
    due_date: datetime | None = None
    action_plan: str | None = None
    closure_evidence_document_id: int | None = None
    closure_note: str | None = None
    closure_verified_at: datetime | None = None


class AuditTrailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mine_id: str
    action_taken: str
    taken_by: str
    timestamp: datetime
    notes: str | None = None


class ScoreHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    safety_score: float
    environmental_score: float
    labor_score: float
    composite_score: float
    risk_band: RiskBand
    reason: str
    timestamp: datetime


class ScoreBreakdown(BaseModel):
    safety: dict
    environmental: dict
    labor: dict
    weights: dict[str, float]


class MineDetail(MineRead):
    score: ComplianceScoreRead
    score_breakdown: ScoreBreakdown
    trend: list[ScoreHistoryRead]
    documents: list[DocumentRead]
    alerts: list[AlertRead]
    audit_trail: list[AuditTrailRead]


class AlertUpdate(BaseModel):
    status: AlertStatus
    taken_by: str = Field(min_length=2, max_length=100)
    notes: str = Field(min_length=2, max_length=1000)
    assigned_to: str | None = Field(default=None, min_length=2, max_length=100)
    due_date: datetime | None = None
    action_plan: str | None = Field(default=None, min_length=6, max_length=1000)
    closure_evidence_document_id: int | None = Field(default=None, ge=1)
    closure_note: str | None = Field(default=None, min_length=8, max_length=1000)


class DemoAlertRequest(BaseModel):
    mine_id: str


class DashboardSummary(BaseModel):
    total_mines: int
    open_alerts: int
    high_risk_mines: int
    documents_reviewed: int
    risk_distribution: dict[str, int]
    state_summary: list[dict]
    critical_demo_active: bool = False
