from __future__ import annotations

import shutil
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .config import PROJECT_ROOT, SAMPLES_DIR, SCORE_WEIGHTS, UPLOADS_DIR
from .database import Base, engine, get_db
from .document_intelligence import IMAGE_SUFFIXES, analyse_document
from .events import create_simulated_alert
from .models import Alert, AuditTrail, ComplianceScore, Document, Mine, ScoreBaseline, ScoreHistory
from .reporting import build_compliance_report
from .schemas import AlertRead, AlertUpdate, DashboardSummary, DemoAlertRequest, DocumentRead, MineCreate, MineDetail, MineListItem
from .scoring import recompute_score, score_breakdown


WEB_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
CRITICAL_DEMO_MINE_ID = "M2881"
CRITICAL_DEMO_PREFIX = "Controlled critical demo scenario:"


def migrate_alert_closure_fields() -> None:
    """Add closure-proof columns to an existing local SQLite demo file.

    This intentionally small additive migration preserves records that may
    already exist on a judge-demo machine without adding a migration framework.
    """
    with engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(alerts)")}
        additions = {
            "closure_evidence_document_id": "INTEGER",
            "closure_note": "TEXT",
            "closure_verified_at": "DATETIME",
        }
        for column, column_type in additions.items():
            if column not in columns:
                connection.exec_driver_sql(f"ALTER TABLE alerts ADD COLUMN {column} {column_type}")


def mine_list_item(mine: Mine) -> dict:
    return {
        "mine_id": mine.mine_id,
        "name": mine.name,
        "state": mine.state,
        "district": mine.district,
        "type": mine.type,
        "operator": mine.operator,
        "score": mine.compliance_score,
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_alert_closure_fields()
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Khadaan Drishti API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/samples", StaticFiles(directory=SAMPLES_DIR), name="samples")


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict:
    return {"status": "ok", "service": "Khadaan Drishti API", "seeded_mines": db.query(Mine).count()}


@app.get("/api/config")
def config() -> dict:
    return {
        "score_weights": SCORE_WEIGHTS,
        "data_notice": "Prototype scope: public mine context is separated from synthetic demonstration scores, documents, and alerts.",
        "feed_notice": "Manual simulation only - no live sensor, CCTV, IoT, or government system is connected.",
    }


@app.get("/api/mines", response_model=list[MineListItem])
def list_mines(
    state: str | None = None,
    risk_band: str | None = Query(default=None, pattern="^(Low|Medium|High)$"),
    mine_type: str | None = Query(default=None, pattern="^(open-cast|underground)$"),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(Mine).join(ComplianceScore).options(joinedload(Mine.compliance_score))
    if state:
        query = query.filter(Mine.state == state)
    if risk_band:
        query = query.filter(ComplianceScore.risk_band == risk_band)
    if mine_type:
        query = query.filter(Mine.type == mine_type)
    mines = query.order_by(ComplianceScore.composite_score.asc(), Mine.name.asc()).all()
    return [mine_list_item(mine) for mine in mines]


@app.post("/api/mines", response_model=MineListItem, status_code=201)
def create_mine(payload: MineCreate, db: Session = Depends(get_db)) -> dict:
    """Create an inspector-entered record with an explicit, traceable starting assessment."""
    mine_id = f"INS-{datetime.utcnow():%Y%m%d}-{uuid4().hex[:5].upper()}"
    now = datetime.utcnow()
    mine = Mine(
        mine_id=mine_id,
        name=payload.name.strip(),
        state=payload.state.strip(),
        district=payload.district.strip(),
        type=payload.type,
        operator=payload.operator.strip(),
        source_reference="Inspector-entered demonstration record - requires authority verification.",
    )
    baseline = ScoreBaseline(
        mine_id=mine_id,
        safety_score=payload.initial_score,
        environmental_score=payload.initial_score,
        labor_score=payload.initial_score,
    )
    score = ComplianceScore(
        mine_id=mine_id,
        safety_score=payload.initial_score,
        environmental_score=payload.initial_score,
        labor_score=payload.initial_score,
        composite_score=payload.initial_score,
        risk_band="Low" if payload.initial_score >= 75 else "Medium" if payload.initial_score >= 50 else "High",
        last_updated=now,
    )
    db.add_all(
        [
            mine,
            baseline,
            score,
            ScoreHistory(
                mine_id=mine_id,
                safety_score=payload.initial_score,
                environmental_score=payload.initial_score,
                labor_score=payload.initial_score,
                composite_score=payload.initial_score,
                risk_band=score.risk_band,
                reason="Inspector-created record: initial assessment",
                timestamp=now,
            ),
            AuditTrail(
                mine_id=mine_id,
                action_taken="Mine profile created",
                taken_by=payload.created_by.strip(),
                notes="Inspector-entered record. Initial score is a prototype assessment pending verified evidence.",
                timestamp=now,
            ),
        ]
    )
    db.commit()
    return mine_list_item(mine)


@app.get("/api/mines/{mine_id}", response_model=MineDetail)
def mine_detail(mine_id: str, db: Session = Depends(get_db)) -> dict:
    mine = (
        db.query(Mine)
        .options(
            joinedload(Mine.compliance_score),
            joinedload(Mine.baseline),
            joinedload(Mine.documents),
            joinedload(Mine.alerts),
            joinedload(Mine.audits),
            joinedload(Mine.score_history),
        )
        .filter(Mine.mine_id == mine_id)
        .first()
    )
    if mine is None:
        raise HTTPException(status_code=404, detail="Mine not found")
    return {
        **mine_list_item(mine),
        "score_breakdown": score_breakdown(mine),
        "trend": sorted(mine.score_history, key=lambda item: item.timestamp)[-12:],
        "documents": sorted(mine.documents, key=lambda item: item.upload_date, reverse=True)[:8],
        "alerts": sorted(mine.alerts, key=lambda item: item.timestamp, reverse=True)[:16],
        "audit_trail": sorted(mine.audits, key=lambda item: item.timestamp, reverse=True)[:16],
    }


@app.get("/api/mines/{mine_id}/report.pdf")
def mine_report(mine_id: str, db: Session = Depends(get_db)) -> Response:
    mine = (
        db.query(Mine)
        .options(
            joinedload(Mine.compliance_score),
            joinedload(Mine.baseline),
            joinedload(Mine.documents),
            joinedload(Mine.alerts),
            joinedload(Mine.audits),
            joinedload(Mine.score_history),
        )
        .filter(Mine.mine_id == mine_id)
        .first()
    )
    if mine is None:
        raise HTTPException(status_code=404, detail="Mine not found")
    pdf = build_compliance_report(mine)
    filename = f"khadaan-drishti-{mine.mine_id.lower()}-compliance-report.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@app.get("/api/alerts")
def list_alerts(
    status: str | None = Query(default=None, pattern="^(open|reviewed|action_taken)$"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(Alert).options(joinedload(Alert.mine))
    if status:
        query = query.filter(Alert.status == status)
    return [
        {
            "id": item.id,
            "mine_id": item.mine_id,
            "mine_name": item.mine.name,
            "event_type": item.event_type,
            "severity": item.severity,
            "timestamp": item.timestamp,
            "status": item.status,
            "description": item.description,
            "assigned_to": item.assigned_to,
            "due_date": item.due_date,
            "action_plan": item.action_plan,
            "closure_evidence_document_id": item.closure_evidence_document_id,
            "closure_note": item.closure_note,
            "closure_verified_at": item.closure_verified_at,
        }
        for item in query.order_by(Alert.timestamp.desc()).limit(limit).all()
    ]


@app.post("/api/alerts/demo", response_model=AlertRead)
def trigger_demo_alert(payload: DemoAlertRequest, db: Session = Depends(get_db)) -> Alert:
    if db.get(Mine, payload.mine_id) is None:
        raise HTTPException(status_code=404, detail="Mine not found")
    try:
        return create_simulated_alert(payload.mine_id, force_high=True)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/demo-scenarios/critical", response_model=AlertRead)
def launch_critical_demo_scenario(db: Session = Depends(get_db)) -> Alert:
    """Activate a single idempotent, clearly labelled high-risk test scenario."""
    existing = (
        db.query(Alert)
        .filter(Alert.description.like(f"{CRITICAL_DEMO_PREFIX}%"))
        .order_by(Alert.timestamp.desc())
        .first()
    )
    if existing:
        return existing
    mine = db.get(Mine, CRITICAL_DEMO_MINE_ID)
    if mine is None:
        raise HTTPException(status_code=500, detail="The controlled demo mine is missing from the seed data.")
    now = datetime.utcnow()
    alert = Alert(
        mine_id=mine.mine_id,
        event_type="emission_spike",
        severity="High",
        status="open",
        description=(
            f"{CRITICAL_DEMO_PREFIX} synthetic particulate-emission observation. "
            "This is a presentation test signal, not a live camera or sensor feed."
        ),
        assigned_to="Environment officer",
        due_date=now + timedelta(hours=24),
        action_plan="Inspect dust suppression controls, capture a follow-up reading, and upload the environmental response note.",
        timestamp=now,
    )
    db.add(alert)
    db.flush()
    recompute_score(db, mine, "Controlled critical demo scenario activated")
    db.commit()
    db.refresh(alert)
    return alert


@app.patch("/api/alerts/{alert_id}", response_model=AlertRead)
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)) -> Alert:
    alert = (
        db.query(Alert)
        .options(
            joinedload(Alert.mine).joinedload(Mine.documents),
            joinedload(Alert.mine).joinedload(Mine.alerts),
            joinedload(Alert.mine).joinedload(Mine.baseline),
        )
        .filter(Alert.id == alert_id)
        .first()
    )
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if payload.status == "action_taken" and alert.status != "action_taken":
        if payload.closure_evidence_document_id is None or payload.closure_note is None:
            raise HTTPException(
                status_code=422,
                detail="Select a mine-linked closure evidence document and add an inspector verification note before closing this action.",
            )
        evidence = db.get(Document, payload.closure_evidence_document_id)
        if evidence is None or evidence.mine_id != alert.mine_id:
            raise HTTPException(status_code=422, detail="Closure evidence must be a document uploaded to this mine record.")
        alert.closure_evidence_document_id = evidence.id
        alert.closure_note = payload.closure_note.strip()
        alert.closure_verified_at = datetime.utcnow()
    status_changed = alert.status != payload.status
    alert.status = payload.status
    if payload.assigned_to is not None:
        alert.assigned_to = payload.assigned_to.strip()
    if payload.due_date is not None:
        alert.due_date = payload.due_date
    if payload.action_plan is not None:
        alert.action_plan = payload.action_plan.strip()
    action_label = "Closure verified with linked evidence" if payload.status == "action_taken" and status_changed else (
        f"Alert marked {payload.status.replace('_', ' ')}" if status_changed else "Corrective action plan updated"
    )
    db.add(
        AuditTrail(
            mine_id=alert.mine_id,
            action_taken=action_label,
            taken_by=payload.taken_by,
            notes=(
                f"{payload.notes} Evidence document #{alert.closure_evidence_document_id}: {alert.closure_note}"
                if payload.status == "action_taken" and status_changed
                else payload.notes
            ),
        )
    )
    if status_changed:
        recompute_score(db, alert.mine, f"Inspector marked alert {payload.status.replace('_', ' ')}")
    db.commit()
    db.refresh(alert)
    return alert


@app.post("/api/documents/upload", response_model=DocumentRead)
def upload_document(
    mine_id: str = Query(...),
    document_type: str = Query(default="Quarterly compliance dossier"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    mine = (
        db.query(Mine)
        .options(joinedload(Mine.documents), joinedload(Mine.alerts), joinedload(Mine.baseline), joinedload(Mine.compliance_score))
        .filter(Mine.mine_id == mine_id)
        .first()
    )
    if mine is None:
        raise HTTPException(status_code=404, detail="Mine not found")
    filename = Path(file.filename or "uploaded_document").name
    suffix = Path(filename).suffix.lower()
    if suffix not in IMAGE_SUFFIXES | {".pdf"}:
        raise HTTPException(status_code=400, detail="Upload a PDF or supported image file.")
    safe_path = UPLOADS_DIR / f"{datetime.utcnow():%Y%m%d%H%M%S}_{uuid4().hex[:8]}_{filename}"
    try:
        with safe_path.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)
        analysis = analyse_document(safe_path)
    except (RuntimeError, ValueError) as error:
        safe_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        file.file.close()
    document = Document(
        mine=mine,
        document_type=document_type,
        checklist_results=analysis["checklist_results"],
        overall_document_status=analysis["overall_document_status"],
        source_filename=filename,
        extracted_text_preview=f"[{analysis['extraction_method']}] {analysis['text_preview']}",
    )
    db.add(document)
    db.flush()
    recompute_score(db, mine, f"Document analysed: {filename}")
    db.commit()
    db.refresh(document)
    return document


@app.get("/api/dashboard", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    scores = db.query(ComplianceScore).all()
    risk_distribution = {band: sum(score.risk_band == band for score in scores) for band in ("Low", "Medium", "High")}
    state_rows = (
        db.query(Mine.state, func.count(Mine.mine_id), func.avg(ComplianceScore.composite_score))
        .join(ComplianceScore)
        .group_by(Mine.state)
        .order_by(func.avg(ComplianceScore.composite_score))
        .all()
    )
    return {
        "total_mines": len(scores),
        "open_alerts": db.query(Alert).filter(Alert.status.in_(["open", "reviewed"])).count(),
        "high_risk_mines": risk_distribution["High"],
        "documents_reviewed": db.query(Document).count(),
        "risk_distribution": risk_distribution,
        "state_summary": [
            {"state": state, "mines": count, "average_score": round(float(average), 1)}
            for state, count, average in state_rows
        ],
        "critical_demo_active": db.query(Alert)
        .filter(Alert.description.like(f"{CRITICAL_DEMO_PREFIX}%"), Alert.status.in_(["open", "reviewed"]))
        .count()
        > 0,
    }


# In deployment, FastAPI serves the already-built React dashboard from the same origin.
# The mount stays last so it never shadows the API or documentation routes.
if WEB_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST_DIR, html=True), name="dashboard")
