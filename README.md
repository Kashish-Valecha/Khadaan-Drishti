# Khadaan Drishti

**Khadaan Drishti (खदान दृष्टि, Mine Vision)** is a demo-grade compliance command centre for coal mines. It demonstrates one complete, auditable loop:

`document upload → checklist result → score recomputation → simulated alert → inspector action → audit trail`

It is built for SIH 2026 problem statement **SIH26024**. It is intentionally not a production surveillance, IoT, or legal-compliance system.

## What is included

- FastAPI + SQLite backend with predictable seed data and a documented API.
- React/Vite/Tailwind inspector and ministry dashboard with Recharts visualizations.
- 24 operating Indian CIL-subsidiary mine records curated from the supplied Global Energy Monitor coal-mine tracker.
- A transparent rules engine: Safety **40%**, Environmental **35%**, Labor **25%**.
- PDF/image document inspection using PDF text extraction first and Tesseract OCR only when necessary.
- A 15-item DGMS/MoEFCC-oriented checklist with regex/fuzzy matches and confidence scores.
- Four seeded corrective actions plus one idempotent, controlled critical-demo scenario - no runaway background alert generation.
- A Compliance Passport for every alert: accountable owner, closure deadline, recommended remedy, linked closure evidence, inspector verification note, and audit history.
- Inspector-created mine records with an initial-assessment score and automatic audit entry.
- Downloadable, evidence-focused PDF compliance snapshots for each mine.
- A visible method/validation panel: transparent 15-clause checklist, OCR scope, curated demo-record count, human-review requirement, and no unsubstantiated accuracy claim.
- A single-service Docker deployment configuration for a public judging URL.

## Quick start (Windows)

Prerequisites: Python 3.11+ and Node.js 20+.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

This one setup command creates the virtual environment, installs both applications, generates the demo files, and seeds the local SQLite database. Start the app with one command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Open `http://127.0.0.1:5173`. API documentation is at `http://127.0.0.1:8000/docs`.

To reset only the database after setup:

```powershell
.\.venv\Scripts\python.exe scripts\seed.py --reset
```

If the virtual environment uses the Unix-style layout, replace `.venv\Scripts\python.exe` with `.venv\bin\python.exe`.

## Deploy a live SIH demo

The repository now includes a one-service Docker deployment. It builds the React dashboard and serves it from the same FastAPI service, so there is no separate frontend URL, proxy setting, or CORS configuration to manage.

1. Create a GitHub repository from this project and push the project files. Do not commit `.venv`, `node_modules`, `data/uploads`, or the local SQLite database.
2. In Render, create a **New Blueprint** from that GitHub repository. It will read [`render.yaml`](render.yaml), build the included [`Dockerfile`](Dockerfile), and publish one web-service URL.
3. Open `<your-service-url>/api/health`; it should return `"status": "ok"` and `"seeded_mines": 24`. Then open the root URL for the dashboard.

The container automatically creates the curated synthetic demo data on its first start. The standard SQLite file is ideal for a judge-facing demo but may reset if a free hosting platform restarts or redeploys the container. For a permanent deployment, replace SQLite with a managed PostgreSQL database and persistent file storage.

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
(cd frontend && npm install)
python scripts/generate_samples.py
python scripts/seed.py --reset
python -m uvicorn app.main:app --app-dir backend --port 8000
```

In a second terminal, run `cd frontend && npm run dev`.

## OCR setup

Digital PDFs work without a local OCR binary. OCR fallback for scanned PDFs/images needs both **Tesseract** and, for scanned PDFs, **Poppler** available on `PATH`.

| Platform | Tesseract | Poppler |
| --- | --- | --- |
| Windows | Install Tesseract from the [UB Mannheim Windows builds](https://github.com/UB-Mannheim/tesseract/wiki) and add its install folder to `PATH`. | Install a Poppler Windows build and add its `Library/bin` (or `bin`) folder to `PATH`. |
| macOS | `brew install tesseract` | `brew install poppler` |
| Ubuntu/Debian | `sudo apt-get install tesseract-ocr` | `sudo apt-get install poppler-utils` |

If OCR tools are not installed, the API gives a clear retry message instead of silently treating a scan as compliant.

## Schema

The required schema lives in [`backend/app/models.py`](backend/app/models.py).

| Entity | Purpose | Key fields |
| --- | --- | --- |
| `Mine` | Mine master data | `mine_id`, name, state, district, type, operator |
| `ComplianceScore` | Current score snapshot | safety, environmental, labor, composite, risk band, timestamp |
| `Document` | Submitted compliance evidence | type, upload date, checklist results, status, filename |
| `Alert` | Simulated violation/anomaly | mine, event type, severity, status, description |
| `AuditTrail` | Inspector decision record | action, actor, time, notes |
| `ScoreHistory` | Chartable score timeline | all score components, band, reason, timestamp |
| `ScoreBaseline` | Stable starting score | prevents repeated recalculation from compounding deductions |

`Document.checklist_results` is a JSON list of `{ clause, found, confidence, category, evidence }`. SQLite remains a single local file at `backend/khadaan_drishti.db`.

## Scoring rules

`composite = safety × 0.40 + environmental × 0.35 + labor × 0.25`

| Band | Composite score |
| --- | --- |
| Low | 75–100 |
| Medium | 50–74.9 |
| High | 0–49.9 |

The score starts from a seeded baseline. The most recently analysed document deducts **2.5 points per missing clause** from its category (capped at 15). Open/reviewed simulated alerts deduct a severity-scaled amount according to their event type. An `action_taken` alert stops contributing its alert deduction, and every recomputation adds a history point. The exact baseline, deductions, and formula appear on the mine page.

Safety is weighted most heavily because immediate injury/loss-of-life exposure requires the fastest governance response. Environmental conditions are next because they combine statutory clearance obligations and long-lived impact. Labor evidence rounds out the score with worker training, PPE, and medical records. These weights are a transparent prototype assumption, not a regulatory formula.

## Checklist orientation

The demo looks for safety officer appointment, safety management, inspection, ventilation, emergency response, maintenance, environmental clearance, six-monthly compliance, air/water monitoring, mine closure, reclamation, training, PPE, and medical records. It uses deterministic keyword/regex matching and a small `difflib` fuzzy-match fallback—no LLM and no trained model.

The checklist is oriented by the [DGMS Coal Mines Regulations, 2017](https://www.dgms.gov.in/writereaddata/UploadFile/CoalMinesRegulation2017.pdf), the [DGMS legislation index](https://www.dgms.gov.in/UserView?mid=1264), and public [PARIVESH/MoEFCC EC conditions](https://parivesh.nic.in/utildoc/1227018318_1778256652717-signed.pdf). It is not a substitute for a mine-specific legal assessment or current approval conditions.

## Data and assumptions

- [`data/mine_catalog.json`](data/mine_catalog.json) contains the 24-mine subset curated from the supplied **Global Coal Mine Tracker, August 2026** in `gem-data.zip`; see [`data/SOURCES.md`](data/SOURCES.md).
- The tracker supplies mine context only. It is **not** used as compliance evidence.
- Every score, document outcome, historical point, alert, and audit entry is synthetic. Events are created only through the controlled demo action; no live or continuously generated feed is claimed.
- Scope has been reconciled with the supplied `Khadaan-Drishti-Project-Description.docx`: four bounded modules, synthetic/public-data-driven demonstration, an explainable score, a 10–15 item checklist, a simulated alert feed, and Inspector/Admin dashboard views. Its technology-stack section is advisory; this implementation uses the user-selected FastAPI, React, and SQLite no-server demo stack.
- No live sensor/CCTV integration, real authentication, mobile/offline mode, blockchain, Kafka, or model training is included by design.

## Demo assets and flow

`data/samples` includes a clean digital PDF, an incomplete digital PDF, and a scanned-style PNG. Use [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for the exact judge-facing click path.

## API surface

| Method | Endpoint | Use |
| --- | --- | --- |
| `GET` | `/api/mines` | Ranked mines with state/risk/type filters |
| `POST` | `/api/mines` | Create a traceable inspector-entered mine profile |
| `GET` | `/api/mines/{mine_id}` | Score explanation, history, docs, alerts, audit trail |
| `GET` | `/api/mines/{mine_id}/report.pdf` | Download the current evidence-focused compliance snapshot |
| `POST` | `/api/documents/upload?mine_id=...` | Analyse a PDF/image and recompute score |
| `GET` | `/api/alerts` | Simulated alert feed |
| `POST` | `/api/alerts/demo` | Fire a High-severity demo alert |
| `POST` | `/api/demo-scenarios/critical` | Launch the idempotent, labelled critical walkthrough scenario |
| `PATCH` | `/api/alerts/{id}` | Mark reviewed or verify closure with linked evidence and audit trail |
| `GET` | `/api/dashboard` | Aggregate dashboard metrics |
