from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Mine(Base):
    __tablename__ = "mines"

    mine_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    operator: Mapped[str] = mapped_column(String(160), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(300))

    compliance_score: Mapped["ComplianceScore"] = relationship(
        back_populates="mine", uselist=False, cascade="all, delete-orphan"
    )
    baseline: Mapped["ScoreBaseline"] = relationship(
        back_populates="mine", uselist=False, cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="mine", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="mine", cascade="all, delete-orphan")
    audits: Mapped[list["AuditTrail"]] = relationship(back_populates="mine", cascade="all, delete-orphan")
    score_history: Mapped[list["ScoreHistory"]] = relationship(back_populates="mine", cascade="all, delete-orphan")


class ComplianceScore(Base):
    __tablename__ = "compliance_scores"

    mine_id: Mapped[str] = mapped_column(ForeignKey("mines.mine_id"), primary_key=True)
    safety_score: Mapped[float] = mapped_column(Float, nullable=False)
    environmental_score: Mapped[float] = mapped_column(Float, nullable=False)
    labor_score: Mapped[float] = mapped_column(Float, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    risk_band: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    mine: Mapped[Mine] = relationship(back_populates="compliance_score")


class ScoreBaseline(Base):
    """Seeded starting point; retained so recalculation never compounds penalties."""

    __tablename__ = "score_baselines"

    mine_id: Mapped[str] = mapped_column(ForeignKey("mines.mine_id"), primary_key=True)
    safety_score: Mapped[float] = mapped_column(Float, nullable=False)
    environmental_score: Mapped[float] = mapped_column(Float, nullable=False)
    labor_score: Mapped[float] = mapped_column(Float, nullable=False)

    mine: Mapped[Mine] = relationship(back_populates="baseline")


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mine_id: Mapped[str] = mapped_column(ForeignKey("mines.mine_id"), index=True)
    safety_score: Mapped[float] = mapped_column(Float, nullable=False)
    environmental_score: Mapped[float] = mapped_column(Float, nullable=False)
    labor_score: Mapped[float] = mapped_column(Float, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_band: Mapped[str] = mapped_column(String(12), nullable=False)
    reason: Mapped[str] = mapped_column(String(160), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    mine: Mapped[Mine] = relationship(back_populates="score_history")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mine_id: Mapped[str] = mapped_column(ForeignKey("mines.mine_id"), index=True)
    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    checklist_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    overall_document_status: Mapped[str] = mapped_column(String(24), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255))
    extracted_text_preview: Mapped[str | None] = mapped_column(Text)

    mine: Mapped[Mine] = relationship(back_populates="documents")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mine_id: Mapped[str] = mapped_column(ForeignKey("mines.mine_id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(100))
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    action_plan: Mapped[str | None] = mapped_column(Text)
    # A closure must reference mine-owned evidence and an inspector verification note.
    closure_evidence_document_id: Mapped[int | None] = mapped_column(Integer)
    closure_note: Mapped[str | None] = mapped_column(Text)
    closure_verified_at: Mapped[datetime | None] = mapped_column(DateTime)

    mine: Mapped[Mine] = relationship(back_populates="alerts")


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mine_id: Mapped[str] = mapped_column(ForeignKey("mines.mine_id"), index=True)
    action_taken: Mapped[str] = mapped_column(String(200), nullable=False)
    taken_by: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    mine: Mapped[Mine] = relationship(back_populates="audits")
