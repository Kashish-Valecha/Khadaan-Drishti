"""Generate local demonstration documents; all content is clearly synthetic."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from PIL import Image, ImageDraw, ImageFilter

from app.demo_content import SAMPLE_FULL_TEXT, SAMPLE_INCOMPLETE_TEXT


SAMPLES = ROOT / "data" / "samples"


def make_pdf(path: Path, title: str, text: str) -> None:
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 20)]
    for paragraph in text.split("\n\n"):
        story.append(Paragraph(paragraph.replace("\n", " "), styles["BodyText"]))
        story.append(Spacer(1, 10))
    SimpleDocTemplate(str(path), pagesize=A4, title=title).build(story)


def make_scanned_image(path: Path) -> None:
    image = Image.new("RGB", (1650, 2200), "#eee9dc")
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 80, 1570, 2120), outline="#807a6d", width=3)
    draw.text((130, 145), "Scanned compliance note - synthetic demo", fill="#292720", font_size=38)
    y = 260
    for line in SAMPLE_FULL_TEXT.splitlines():
        if line.strip():
            draw.text((140, y), line[:84], fill="#3d3931", font_size=25)
            y += 58
    image = image.rotate(0.4, fillcolor="#eee9dc").filter(ImageFilter.GaussianBlur(radius=0.25))
    image.save(path)


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    make_pdf(SAMPLES / "clean_compliance_dossier.pdf", "Clean compliance dossier", SAMPLE_FULL_TEXT)
    make_pdf(SAMPLES / "incomplete_quarterly_submission.pdf", "Incomplete quarterly submission", SAMPLE_INCOMPLETE_TEXT)
    make_scanned_image(SAMPLES / "scanned_style_compliance_note.png")
    print(f"Generated demo samples in {SAMPLES}")


if __name__ == "__main__":
    main()
