"""Create a predictable, synthetic demo database from the curated GEM mine catalog."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.checklist import document_status, match_checklist
from app.database import Base, SessionLocal, engine
from app.demo_content import SAMPLE_FULL_TEXT, SAMPLE_INCOMPLETE_TEXT
from app.events import ACTION_OWNERS, ACTION_PLANS
from app.models import Alert, ComplianceScore, Document, Mine, ScoreBaseline, ScoreHistory
from app.scoring import recompute_score, risk_band


BASELINES = [
    (91, 88, 92), (86, 87, 90), (90, 84, 88), (84, 85, 86),
    (82, 80, 84), (86, 83, 81), (80, 79, 83), (78, 82, 79),
    (77, 75, 78), (74, 76, 74), (77, 71, 75), (73, 74, 76),
    (76, 72, 73), (71, 74, 70), (75, 70, 74), (72, 72, 71),
    (70, 66, 70), (69, 67, 72), (67, 68, 65), (72, 65, 68),
    (66, 64, 69), (69, 62, 66), (65, 67, 63), (68, 63, 65),
]

INITIAL_ALERTS = {
    "M2881": ("worker_without_safety_gear", "High", "PPE non-compliance observed during a simulated underground shift."),
    "M0632": ("emission_spike", "High", "Simulated particulate emission exceeded the configured threshold."),
    "M0634": ("truck_overload", "Medium", "Simulated haul-truck overload detected at the weighbridge."),
    "M0556": ("boundary_breach", "Medium", "Simulated vehicle movement crossed the approved mining boundary."),
}


def historical_score(base: tuple[int, int, int], offset: int) -> tuple[float, float, float]:
    return tuple(max(0, min(100, value + offset)) for value in base)


def add_history(db, mine_id: str, values: tuple[float, float, float], when: datetime, reason: str) -> None:
    safety, environmental, labor = values
    composite = round(safety * 0.40 + environmental * 0.35 + labor * 0.25, 1)
    db.add(
        ScoreHistory(
            mine_id=mine_id,
            safety_score=safety,
            environmental_score=environmental,
            labor_score=labor,
            composite_score=composite,
            risk_band=risk_band(composite),
            reason=reason,
            timestamp=when,
        )
    )


def seed(reset: bool) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Mine).first():
            print("Database already contains mines. Use --reset to rebuild it.")
            return
        catalog = json.loads((ROOT / "data" / "mine_catalog.json").read_text(encoding="utf-8"))
        now = datetime.utcnow()
        for index, item in enumerate(catalog):
            baseline_values = BASELINES[index]
            mine = Mine(
                mine_id=item["mine_id"],
                name=item["name"],
                state=item["state"],
                district=item["district"],
                type=item["type"],
                operator=item["operator"],
                source_reference="Global Energy Monitor, Global Coal Mine Tracker, August 2026 (supplied dataset)",
            )
            db.add(mine)
            db.add(ScoreBaseline(mine_id=mine.mine_id, safety_score=baseline_values[0], environmental_score=baseline_values[1], labor_score=baseline_values[2]))
            initial_composite = round(baseline_values[0] * 0.40 + baseline_values[1] * 0.35 + baseline_values[2] * 0.25, 1)
            db.add(ComplianceScore(mine_id=mine.mine_id, safety_score=baseline_values[0], environmental_score=baseline_values[1], labor_score=baseline_values[2], composite_score=initial_composite, risk_band=risk_band(initial_composite), last_updated=now))
            for weeks_ago, offset in [(12, -3), (8, -1), (4, 1)]:
                add_history(db, mine.mine_id, historical_score(baseline_values, offset), now - timedelta(weeks=weeks_ago), "Synthetic historical checkpoint")

            document_text = SAMPLE_INCOMPLETE_TEXT if index in {18, 20, 21, 22} else SAMPLE_FULL_TEXT
            results = match_checklist(document_text)
            db.add(
                Document(
                    mine_id=mine.mine_id,
                    document_type="Quarterly compliance dossier",
                    upload_date=now - timedelta(days=(index % 15) + 2),
                    checklist_results=results,
                    overall_document_status=document_status(results),
                    source_filename="seeded_synthetic_submission.pdf",
                    extracted_text_preview="Synthetic seed document. " + document_text[:500],
                )
            )
        db.flush()
        for mine_id, (event_type, severity, description) in INITIAL_ALERTS.items():
            db.add(
                Alert(
                    mine_id=mine_id,
                    event_type=event_type,
                    severity=severity,
                    status="open",
                    description=description,
                    assigned_to=ACTION_OWNERS[event_type],
                    due_date=now + timedelta(days=1 if severity == "High" else 3),
                    action_plan=ACTION_PLANS[event_type],
                    timestamp=now - timedelta(hours=2),
                )
            )
        db.flush()
        for mine in db.query(Mine).all():
            recompute_score(db, mine, "Initial synthetic score computation")
        db.commit()
        print(f"Seeded {len(catalog)} mines, {len(INITIAL_ALERTS)} simulated alerts, and score history.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Rebuild the SQLite demo database")
    seed(reset=parser.parse_args().reset)
