"""Small, deliberately simulated alert feed for the demo."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from .database import SessionLocal
from .models import Alert, Mine
from .scoring import recompute_score


EVENTS = {
    "truck_overload": "Simulated weighbridge alert: haul truck payload is above the configured limit.",
    "worker_without_safety_gear": "Simulated PPE observation: a worker was recorded without required safety gear.",
    "boundary_breach": "Simulated geofence event: vehicle movement crossed the approved mining boundary.",
    "emission_spike": "Simulated monitoring event: particulate emission exceeded the configured threshold.",
}

# Suggested ownership and remedy make a simulated signal into a judge-visible action workflow.
ACTION_OWNERS = {
    "truck_overload": "Haulage supervisor",
    "worker_without_safety_gear": "Mine safety officer",
    "boundary_breach": "Operations manager",
    "emission_spike": "Environment officer",
}
ACTION_PLANS = {
    "truck_overload": "Verify payload calibration, remove the overloaded vehicle from service, and record corrective briefing.",
    "worker_without_safety_gear": "Stop the task, issue required PPE, conduct a toolbox talk, and upload the supervisor sign-off.",
    "boundary_breach": "Verify the geofence exception, inspect the route, and record an approved corrective movement plan.",
    "emission_spike": "Inspect dust suppression controls, capture a follow-up reading, and upload the environmental response note.",
}


def create_simulated_alert(mine_id: str, *, force_high: bool = False) -> Alert:
    db = SessionLocal()
    try:
        mine = db.get(Mine, mine_id)
        if mine is None:
            raise ValueError(f"Mine {mine_id} was not found")
        event_type = random.choice(list(EVENTS))
        severity = "High" if force_high else random.choices(["Low", "Medium", "High"], weights=[4, 4, 2])[0]
        now = datetime.utcnow()
        alert = Alert(
            mine_id=mine_id,
            event_type=event_type,
            severity=severity,
            status="open",
            description=EVENTS[event_type],
            assigned_to=ACTION_OWNERS[event_type],
            due_date=now + timedelta(hours=24 if severity == "High" else 72),
            action_plan=ACTION_PLANS[event_type],
        )
        db.add(alert)
        db.flush()
        recompute_score(db, mine, f"Simulated {severity.lower()} alert: {event_type.replace('_', ' ')}")
        db.commit()
        db.refresh(alert)
        return alert
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
