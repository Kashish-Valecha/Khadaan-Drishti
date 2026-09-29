"""Deterministic, inspectable score recomputation rules."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from .config import RISK_BANDS, SCORE_WEIGHTS
from .models import Alert, ComplianceScore, Document, Mine, ScoreHistory


ALERT_PENALTIES = {
    "truck_overload": {"safety": 7, "environmental": 1, "labor": 0},
    "worker_without_safety_gear": {"safety": 10, "environmental": 0, "labor": 4},
    "boundary_breach": {"safety": 2, "environmental": 8, "labor": 0},
    "emission_spike": {"safety": 0, "environmental": 12, "labor": 0},
}
SEVERITY_MULTIPLIER = {"Low": 0.45, "Medium": 0.75, "High": 1.0}
DOCUMENT_MISSING_PENALTY = 2.5
DOCUMENT_PENALTY_CAP = 15.0


def risk_band(composite_score: float) -> str:
    for threshold, band in RISK_BANDS:
        if composite_score >= threshold:
            return band
    return "High"


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _latest_document(mine: Mine) -> Document | None:
    return max(mine.documents, key=lambda document: document.upload_date) if mine.documents else None


def calculate_score(mine: Mine) -> tuple[dict[str, float], dict]:
    if not mine.baseline:
        raise ValueError(f"Mine {mine.mine_id} has no score baseline")

    components = {
        "safety": mine.baseline.safety_score,
        "environmental": mine.baseline.environmental_score,
        "labor": mine.baseline.labor_score,
    }
    deductions: dict[str, list[dict]] = defaultdict(list)

    latest_document = _latest_document(mine)
    if latest_document:
        missing_by_category: dict[str, int] = defaultdict(int)
        for item in latest_document.checklist_results:
            if not item.get("found"):
                missing_by_category[item["category"]] += 1
        for category, count in missing_by_category.items():
            penalty = min(DOCUMENT_PENALTY_CAP, count * DOCUMENT_MISSING_PENALTY)
            components[category] -= penalty
            deductions[category].append(
                {
                    "source": "latest document",
                    "label": f"{count} checklist item(s) missing",
                    "points": round(penalty, 1),
                }
            )

    active_alerts = [alert for alert in mine.alerts if alert.status in {"open", "reviewed"}]
    for alert in active_alerts:
        for category, raw_penalty in ALERT_PENALTIES.get(alert.event_type, {}).items():
            penalty = round(raw_penalty * SEVERITY_MULTIPLIER[alert.severity], 1)
            if penalty:
                components[category] -= penalty
                deductions[category].append(
                    {
                        "source": "simulated alert",
                        "label": f"{alert.severity} {alert.event_type.replace('_', ' ')}",
                        "points": penalty,
                    }
                )

    components = {category: _clamp(value) for category, value in components.items()}
    composite = round(sum(components[category] * SCORE_WEIGHTS[category] for category in SCORE_WEIGHTS), 1)
    explanation = {
        category: {
            "baseline": round(getattr(mine.baseline, f"{category}_score"), 1),
            "score": components[category],
            "deductions": deductions[category],
        }
        for category in components
    }
    explanation["weights"] = SCORE_WEIGHTS
    explanation["formula"] = "Safety × 40% + Environmental × 35% + Labor × 25%"
    return {**components, "composite": composite, "risk_band": risk_band(composite)}, explanation


def score_breakdown(mine: Mine) -> dict:
    _, explanation = calculate_score(mine)
    return explanation


def recompute_score(db: Session, mine: Mine, reason: str) -> ComplianceScore:
    values, _ = calculate_score(mine)
    score = mine.compliance_score
    now = datetime.utcnow()
    if score is None:
        score = ComplianceScore(mine_id=mine.mine_id, safety_score=0, environmental_score=0, labor_score=0, composite_score=0, risk_band="High")
        db.add(score)
    score.safety_score = values["safety"]
    score.environmental_score = values["environmental"]
    score.labor_score = values["labor"]
    score.composite_score = values["composite"]
    score.risk_band = values["risk_band"]
    score.last_updated = now
    db.add(
        ScoreHistory(
            mine_id=mine.mine_id,
            safety_score=score.safety_score,
            environmental_score=score.environmental_score,
            labor_score=score.labor_score,
            composite_score=score.composite_score,
            risk_band=score.risk_band,
            reason=reason,
            timestamp=now,
        )
    )
    db.flush()
    return score
