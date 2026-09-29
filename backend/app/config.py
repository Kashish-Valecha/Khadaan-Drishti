from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
UPLOADS_DIR = DATA_DIR / "uploads"
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'backend' / 'khadaan_drishti.db'}"

# These weights are intentionally kept in one readable location for auditability.
SCORE_WEIGHTS = {
    "safety": 0.40,
    "environmental": 0.35,
    "labor": 0.25,
}

RISK_BANDS = (
    (75, "Low"),
    (50, "Medium"),
    (0, "High"),
)

CHECKLIST_VERSION = "2026.1-demo"
