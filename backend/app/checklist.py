"""Transparent document checklist matching without an LLM or trained model."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .config import CHECKLIST_VERSION


CHECKLIST = [
    {
        "key": "safety_officer",
        "clause": "Safety officer appointment recorded",
        "category": "safety",
        "patterns": [r"safety officer.{0,50}(appointed|appointment|designated)", r"appointed safety officer"],
        "phrases": ["safety officer appointed", "appointment of safety officer"],
    },
    {
        "key": "safety_management_plan",
        "clause": "Safety management plan available",
        "category": "safety",
        "patterns": [r"safety management plan", r"smp.{0,40}(approved|reviewed|available)"],
        "phrases": ["approved safety management plan"],
    },
    {
        "key": "inspection_records",
        "clause": "Statutory inspection records maintained",
        "category": "safety",
        "patterns": [r"statutory inspection.{0,45}(record|register|log)", r"inspection register"],
        "phrases": ["statutory inspection records"],
    },
    {
        "key": "ventilation_plan",
        "clause": "Ventilation plan and survey evidence available",
        "category": "safety",
        "patterns": [r"ventilation (plan|survey|circuit)", r"air quantity.{0,45}(measured|survey|record)"],
        "phrases": ["ventilation survey completed"],
    },
    {
        "key": "emergency_response",
        "clause": "Emergency response drill records available",
        "category": "safety",
        "patterns": [r"emergency (response|preparedness).{0,45}(drill|exercise|plan)", r"mock drill"],
        "phrases": ["emergency response drill"],
    },
    {
        "key": "maintenance_register",
        "clause": "Equipment maintenance and testing records maintained",
        "category": "safety",
        "patterns": [r"(equipment|machinery).{0,45}(maintenance|inspection|testing) (record|register|log)", r"preventive maintenance register"],
        "phrases": ["equipment maintenance records"],
    },
    {
        "key": "environmental_clearance",
        "clause": "Environmental clearance reference present",
        "category": "environmental",
        "patterns": [r"environmental clearance", r"ec (condition|letter|compliance)"],
        "phrases": ["environmental clearance condition"],
    },
    {
        "key": "six_monthly_compliance",
        "clause": "Six-monthly environmental compliance report submitted",
        "category": "environmental",
        "patterns": [r"six[- ]?monthly compliance", r"half[- ]?yearly compliance"],
        "phrases": ["six monthly compliance report"],
    },
    {
        "key": "air_quality",
        "clause": "Ambient air quality monitoring reported",
        "category": "environmental",
        "patterns": [r"(ambient )?air quality.{0,45}(monitor|report|result)", r"particulate matter.{0,45}(monitor|report)"],
        "phrases": ["ambient air quality monitoring"],
    },
    {
        "key": "water_monitoring",
        "clause": "Water quality or groundwater monitoring reported",
        "category": "environmental",
        "patterns": [r"(water quality|groundwater).{0,45}(monitor|report|sample)", r"effluent monitoring"],
        "phrases": ["water quality monitoring"],
    },
    {
        "key": "mine_closure",
        "clause": "Progressive or final mine closure plan available",
        "category": "environmental",
        "patterns": [r"(progressive|final)? ?mine closure plan", r"closure plan.{0,45}(approved|reviewed|attached)"],
        "phrases": ["progressive mine closure plan"],
    },
    {
        "key": "reclamation",
        "clause": "Reclamation or green-belt progress reported",
        "category": "environmental",
        "patterns": [r"(reclamation|rehabilitation|green belt).{0,45}(progress|report|plan)", r"overburden.{0,45}(reclaim|dump)"],
        "phrases": ["land reclamation progress"],
    },
    {
        "key": "training_records",
        "clause": "Worker training records maintained",
        "category": "labor",
        "patterns": [r"(worker|employee|contractor).{0,45}(training|induction).{0,45}(record|register|log)", r"vocational training record"],
        "phrases": ["worker training records"],
    },
    {
        "key": "ppe_register",
        "clause": "PPE issue or compliance register maintained",
        "category": "labor",
        "patterns": [r"(ppe|personal protective equipment).{0,45}(issue|compliance|register)", r"safety gear register"],
        "phrases": ["personal protective equipment register"],
    },
    {
        "key": "medical_records",
        "clause": "Periodic medical examination records maintained",
        "category": "labor",
        "patterns": [r"(periodic )?medical examination.{0,45}(record|register|report)", r"occupational health.{0,45}(record|screening)"],
        "phrases": ["periodic medical examination records"],
    },
]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _evidence(text: str, start: int, end: int) -> str:
    return text[max(0, start - 55) : min(len(text), end + 105)].strip()


def _best_fuzzy_match(text: str, phrases: list[str]) -> tuple[float, str | None]:
    words = text.split()
    best_score, best_window = 0.0, None
    for phrase in phrases:
        size = len(phrase.split())
        for index in range(max(0, len(words) - size + 1)):
            window = " ".join(words[index : index + size + 3])
            score = SequenceMatcher(None, phrase, window).ratio()
            if score > best_score:
                best_score, best_window = score, window
    return best_score, best_window


def match_checklist(text: str) -> list[dict]:
    """Return one explainable match result per required demo clause."""
    normalised = _normalise(text)
    results: list[dict] = []
    for item in CHECKLIST:
        found_match = None
        for pattern in item["patterns"]:
            found_match = re.search(pattern, normalised, flags=re.IGNORECASE)
            if found_match:
                break
        if found_match:
            results.append(
                {
                    "clause": item["clause"],
                    "found": True,
                    "confidence": 0.98,
                    "category": item["category"],
                    "evidence": _evidence(normalised, found_match.start(), found_match.end()),
                    "match_method": "regex",
                    "checklist_version": CHECKLIST_VERSION,
                }
            )
            continue
        fuzzy_score, window = _best_fuzzy_match(normalised, item["phrases"])
        found = fuzzy_score >= 0.84
        results.append(
            {
                "clause": item["clause"],
                "found": found,
                "confidence": round(fuzzy_score if found else max(0.05, fuzzy_score * 0.45), 2),
                "category": item["category"],
                "evidence": window if found else None,
                "match_method": "fuzzy" if found else "not_found",
                "checklist_version": CHECKLIST_VERSION,
            }
        )
    return results


def document_status(results: list[dict]) -> str:
    missing = sum(not item["found"] for item in results)
    if missing == 0:
        return "compliant"
    if missing <= 3:
        return "needs_review"
    return "incomplete"
