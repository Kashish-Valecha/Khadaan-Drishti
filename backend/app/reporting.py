"""Printable, evidence-focused compliance dossier for the judge-facing workflow."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Mine
from .scoring import score_breakdown


COAL = colors.HexColor("#294144")
AMBER = colors.HexColor("#D9950B")
MUTED = colors.HexColor("#5E6C76")
RISK_COLORS = {"Low": colors.HexColor("#198754"), "Medium": AMBER, "High": colors.HexColor("#C94740")}


def _date(value: datetime) -> str:
    return value.strftime("%d %b %Y, %H:%M UTC")


def _cell(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(value)), style)


def _header_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#DCE4E5"))
    canvas.line(18 * mm, 12 * mm, A4[0] - 18 * mm, 12 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 7.5 * mm, "Khadaan Drishti - AI-assisted compliance demonstration")
    canvas.drawRightString(A4[0] - 18 * mm, 7.5 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_compliance_report(mine: Mine) -> bytes:
    """Return a polished PDF generated from the currently loaded mine relations."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Compliance report - {mine.name}",
        author="Khadaan Drishti",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=19, leading=24, textColor=COAL, spaceAfter=3)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=MUTED)
    heading = ParagraphStyle("SectionHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=COAL, spaceBefore=14, spaceAfter=7)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#26343D"))
    small = ParagraphStyle("Small", parent=body, fontSize=8, leading=11, textColor=MUTED)
    right = ParagraphStyle("Right", parent=body, alignment=TA_RIGHT, fontName="Helvetica-Bold")
    story = [
        Paragraph("KHADAAN DRISHTI", subtitle),
        Paragraph("Mine Compliance Snapshot", title),
        Paragraph("Inspector-ready report generated from the current local project record. It supports review and does not certify statutory compliance.", subtitle),
        Spacer(1, 10),
    ]

    profile = [
        [_cell("Mine", small), _cell(mine.name, body), _cell("Mine ID", small), _cell(mine.mine_id, body)],
        [_cell("Location", small), _cell(f"{mine.district}, {mine.state}", body), _cell("Mine type", small), _cell(mine.type.replace("-", " ").title(), body)],
        [_cell("Operator", small), _cell(mine.operator, body), _cell("Report generated", small), _cell(_date(datetime.utcnow()), body)],
    ]
    profile_table = Table(profile, colWidths=[24 * mm, 60 * mm, 29 * mm, 52 * mm])
    profile_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F8F8")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE4E5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E6ECEC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([Paragraph("Mine profile", heading), profile_table])

    score = mine.compliance_score
    breakdown = score_breakdown(mine)
    score_rows = [
        [_cell("Composite compliance score", small), _cell(f"{score.composite_score} / 100", right), _cell("Risk band", small), _cell(score.risk_band, right)],
        [_cell("Safety", small), _cell(f"{score.safety_score} (weight 40%)", right), _cell("Environmental", small), _cell(f"{score.environmental_score} (weight 35%)", right)],
        [_cell("Labor", small), _cell(f"{score.labor_score} (weight 25%)", right), _cell("Last recalculated", small), _cell(_date(score.last_updated), right)],
    ]
    score_table = Table(score_rows, colWidths=[47 * mm, 35 * mm, 42 * mm, 41 * mm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F8F8")),
        ("BOX", (0, 0), (-1, -1), 0.5, RISK_COLORS[score.risk_band]),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E6ECEC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([Paragraph("Explainable score", heading), score_table, Paragraph(escape(breakdown["formula"]), small)])

    latest = max(mine.documents, key=lambda item: item.upload_date) if mine.documents else None
    story.append(Paragraph("Evidence checklist", heading))
    if latest:
        found = [item for item in latest.checklist_results if item.get("found")]
        missing = [item for item in latest.checklist_results if not item.get("found")]
        story.append(Paragraph(
            escape(f"Latest submission: {latest.source_filename or 'uploaded document'} - {len(found)}/15 checks located - {latest.overall_document_status.replace('_', ' ')}."),
            body,
        ))
        rows = [[_cell("Status", small), _cell("Checklist clause", small), _cell("Category", small), _cell("Evidence", small)]]
        for item in latest.checklist_results:
            rows.append([
                _cell("FOUND" if item.get("found") else "MISSING", body),
                _cell(item.get("clause", ""), body),
                _cell(item.get("category", "").title(), body),
                _cell(item.get("evidence") or "No matching text located", small),
            ])
        checks = Table(rows, colWidths=[20 * mm, 50 * mm, 25 * mm, 69 * mm], repeatRows=1)
        checklist_style = [
            ("BACKGROUND", (0, 0), (-1, 0), COAL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DCE4E5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for row, item in enumerate(latest.checklist_results, start=1):
            checklist_style.append(("BACKGROUND", (0, row), (0, row), colors.HexColor("#ECF8F1") if item.get("found") else colors.HexColor("#FDF1F0")))
        checks.setStyle(TableStyle(checklist_style))
        story.append(Spacer(1, 6))
        story.append(checks)
    else:
        story.append(Paragraph("No document has been uploaded for this mine. Upload a PDF or supported image to produce a transparent checklist result.", body))

    story.append(Paragraph("Compliance passport and audit trail", heading))
    active_alerts = [alert for alert in mine.alerts if alert.status in {"open", "reviewed"}]
    if active_alerts:
        for alert in sorted(active_alerts, key=lambda item: item.timestamp, reverse=True)[:6]:
            deadline = _date(alert.due_date) if alert.due_date else "No deadline set"
            story.append(Paragraph(escape(f"{alert.severity} - {alert.event_type.replace('_', ' ')}: {alert.description} ({alert.status.replace('_', ' ')})"), body))
            story.append(Paragraph(escape(f"Owner: {alert.assigned_to or 'Unassigned'} | Deadline: {deadline} | Required action: {alert.action_plan or 'Human review required.'}"), small))
    else:
        story.append(Paragraph("No open or reviewed alerts are currently recorded.", body))
    verified_closures = [alert for alert in mine.alerts if alert.status == "action_taken" and alert.closure_evidence_document_id]
    if verified_closures:
        story.append(Paragraph("Verified closures", heading))
        document_names = {document.id: document.source_filename or f"Document #{document.id}" for document in mine.documents}
        for alert in sorted(verified_closures, key=lambda item: item.closure_verified_at or item.timestamp, reverse=True)[:6]:
            evidence_name = document_names.get(alert.closure_evidence_document_id, f"Document #{alert.closure_evidence_document_id}")
            verified_at = _date(alert.closure_verified_at) if alert.closure_verified_at else "Recorded time unavailable"
            story.append(Paragraph(escape(f"{alert.event_type.replace('_', ' ').title()} — evidence: {evidence_name}."), body))
            story.append(Paragraph(escape(f"Inspector verification: {alert.closure_note or 'No note recorded.'} | Verified: {verified_at}"), small))
    for audit in sorted(mine.audits, key=lambda item: item.timestamp, reverse=True)[:5]:
        story.append(Paragraph(escape(f"{_date(audit.timestamp)} - {audit.action_taken} by {audit.taken_by}. {audit.notes or ''}"), small))

    story.extend([
        Paragraph("Scope note", heading),
        Paragraph("This report is generated by an AI-assisted prototype rules engine. The checklist uses uploaded text or OCR-derived text, while alerts are manual simulations in this demonstration. A competent authority must validate mine-specific statutory requirements and evidence before any compliance decision.", body),
    ])
    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output.getvalue()
