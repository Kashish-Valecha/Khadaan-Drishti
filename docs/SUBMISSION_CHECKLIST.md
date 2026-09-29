# Submission Checklist - Khadaan Drishti

## Before publishing the link

- Run the local dashboard and check `http://127.0.0.1:5173`.
- Confirm `http://127.0.0.1:8000/api/health` reports `status: ok` and `seeded_mines: 24`.
- Use **Launch critical demo** once. Confirm Moonidih appears as a clearly labelled synthetic High-risk scenario with an owner and deadline.
- Open Moonidih, select/upload mine-linked closure evidence, add an inspector verification note, and confirm the API blocks **Verify & close** until both are supplied.
- Create one mine with **Add mine**, open it, and download its compliance report.
- Do not describe simulated alerts or scores as live regulatory data. The interface and pitch should say **AI-assisted prototype using curated/public context and synthetic demonstration signals**.

## Public URL in Render

1. Push this project to a GitHub repository.
2. In Render, select **New +**, then **Blueprint**, and select the GitHub repository.
3. Render reads `render.yaml` and builds the included `Dockerfile`. No separate frontend service is required.
4. Once the build succeeds, open the root URL and then `<your-url>/api/health`.
5. Put the resulting URL in the project submission and presentation.

The first hosted start seeds the 24 curated-context mines automatically. A free container may reset its SQLite data after a restart; this is acceptable for a judging demonstration but must be replaced with managed PostgreSQL and persistent storage for a field deployment.

## Files to submit

- Source repository or ZIP, including `README.md`.
- Public dashboard URL, if the hosting account is available.
- `docs/DEMO_SCRIPT.md` for the exact judging path.
- A 6-8 slide presentation: problem, users, solution, live workflow, AI/rules explanation, architecture, impact, and roadmap.
- A 90-120 second screen recording as a fallback if network access is unavailable during judging.

## Suggested final pitch

"Khadaan Drishti is an explainable mine-compliance command centre. It helps inspectors create a mine record, analyse document evidence against a transparent checklist, prioritise compliance risk, close corrective actions with an audit trail, and export a concise compliance snapshot. It is designed as a responsible prototype: public mine context is separated from synthetic demo signals, and final compliance decisions remain with competent authorities."
