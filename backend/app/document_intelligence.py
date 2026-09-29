"""Local PDF/image extraction with a digital-PDF-first OCR fallback."""

from __future__ import annotations

from pathlib import Path

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from .checklist import document_status, match_checklist


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def _ocr_pdf(path: Path) -> str:
    pages = convert_from_path(path, dpi=220)
    return "\n".join(pytesseract.image_to_string(page) for page in pages)


def extract_text(path: Path) -> tuple[str, str]:
    """Extract text and identify the extraction method for the audit preview."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with pdfplumber.open(path) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
        if len(text.strip()) >= 40:
            return text, "pdf_text_layer"
        try:
            return _ocr_pdf(path), "ocr_fallback"
        except Exception as error:  # pragma: no cover - depends on local Poppler/Tesseract install
            raise RuntimeError(
                "The PDF has no readable text layer and OCR is unavailable. Install Tesseract and Poppler, then retry."
            ) from error
    if suffix in IMAGE_SUFFIXES:
        try:
            with Image.open(path) as image:
                return pytesseract.image_to_string(image), "ocr_image"
        except Exception as error:  # pragma: no cover - depends on local Tesseract install
            raise RuntimeError("OCR is unavailable. Install Tesseract, then retry.") from error
    raise ValueError("Supported uploads are PDF, PNG, JPG, JPEG, TIFF, and BMP files.")


def analyse_document(path: Path) -> dict:
    text, extraction_method = extract_text(path)
    results = match_checklist(text)
    return {
        "checklist_results": results,
        "overall_document_status": document_status(results),
        "text_preview": " ".join(text.split())[:900],
        "extraction_method": extraction_method,
    }
