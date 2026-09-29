# Khadaan Drishti Demo Script

Use the **two-minute core flow** for the first judging round. Keep the remaining details ready for questions.

## Two-minute core flow

1. **Start with the problem** - In **Inspector** view, say: *"Mines have documents, observations, and pending actions in different places. Khadaan Drishti turns them into one explainable compliance workflow."* Point out the data notice: mine context is curated from the supplied GEM tracker; scores and alerts are clearly marked synthetic in this prototype.
2. **Create a record** - Click **Add mine**, enter a mine name/location/operator and an initial assessment, then click **Create mine profile**. Show the automatically created score-history point and audit entry. Explain that the record is marked as inspector-entered until verified.
3. **Explain the AI-assisted evidence check** - Open a High-risk mine, preferably **Moonidih Coal Mine**, and select **Use incomplete demo PDF**. Show that the system extracts text, locates the 15 checklist clauses, names the missing evidence, and explains the changed 40/35/25 score.
4. **Close the loop** - Use **Launch critical demo** on the dashboard. It activates one labelled synthetic High-risk emission-control scenario for Moonidih; it is not a live sensor signal. Open the mine record, show its **Compliance Passport**, upload/select a mine-linked closure document, write the inspector verification note, then choose **Verify & close**. Download the report to show the resulting evidence-to-action trail.

## Backup walkthrough for questions

1. **Portfolio view** - Switch to **Admin / Ministry**. Show the risk-distribution donut and state compliance bar chart. Switch back to **Inspector**.
2. **Explain the trend** - Point out the trend-chart tooltips. Historical points are seeded demonstration checkpoints; every document or action creates a new score-history point.
3. **Explain alerts** - Events are manual test signals, not a live feed. Each one immediately receives an owner, due date, remedy, visible component deduction, and audit entry. An action cannot close until a mine-linked evidence document and inspector verification note are supplied. When verified and closed, it stops contributing its active-alert deduction.
4. **OCR** - Digital PDFs use their text layer first. OCR is only used when a PDF lacks text; use `scanned_style_compliance_note.png` as the scan example.

Talking points:

- It is not a black-box score. The exact formula, every deduction, matching evidence phrases, and a 15-clause method trace are visible.
- The demo intentionally omits real IoT, CCTV, login, Kafka, and model training. Those are future integration points, not claims made by this prototype.
- OCR is used only when a PDF lacks a text layer; scanned images can be tested with `scanned_style_compliance_note.png`.
