from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

from fastapi import UploadFile

from courter_shared.schemas import ContradictionReport, StructuredEvidence

from ..config import get_settings
from .audit import audit


SUPPORTED_MIME = {"application/pdf", "image/png", "image/jpeg", "text/plain"}
EVIDENCE_KEYWORDS = {
    "certificate",
    "registry",
    "agreement",
    "contract",
    "receipt",
    "transfer",
    "ownership",
    "tenant",
    "landlord",
    "inheritance",
    "will",
    "property",
    "rent",
    "payment",
    "date",
    "signed",
}


async def extract_text(file: UploadFile, case_id: str, actor_id: str) -> dict:
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        audit("evidence_upload_rejected", actor_type="user", actor_id=actor_id, entity_type="case", entity_id=case_id, severity="warning", metadata={"file": file.filename, "reason": "too_large"})
        raise ValueError("Evidence file is too large.")
    if file.content_type not in SUPPORTED_MIME:
        audit("evidence_upload_rejected", actor_type="user", actor_id=actor_id, entity_type="case", entity_id=case_id, severity="warning", metadata={"file": file.filename, "mime": file.content_type})
        raise ValueError("Evidence type is not supported.")

    text = ""
    method = "direct"
    degraded = False
    if file.content_type == "text/plain":
        text = data.decode("utf-8", errors="ignore")
    elif file.content_type == "application/pdf":
        method = "pdf-text"
        text = _extract_pdf_text(data)
        if not clean_text(text):
            method = "pdf-ocr"
            text = _ocr_pdf_bytes(data)
        if not clean_text(text):
            method = "ocr-degraded-fallback"
            degraded = True
            text = ""
    else:
        method = "image-ocr"
        text = _ocr_image_bytes(data)
        if not clean_text(text):
            method = "ocr-degraded-fallback"
            degraded = True
            text = ""

    cleaned = clean_text(text)
    audit("ocr_completed", actor_type="user", actor_id=actor_id, entity_type="case", entity_id=case_id, metadata={"file": file.filename, "method": method, "chars": len(cleaned), "degraded": degraded})
    return {"filename": file.filename, "mime_type": file.content_type, "text": cleaned, "ocr_method": method, "ocr_degraded": degraded, "size": len(data)}


def _extract_pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(data))
        return " ".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def _ocr_image_bytes(data: bytes) -> str:
    if not shutil.which("tesseract"):
        return ""
    try:
        from PIL import Image
        import pytesseract
        import io

        return pytesseract.image_to_string(Image.open(io.BytesIO(data)))
    except Exception:
        return ""


def _ocr_pdf_bytes(data: bytes) -> str:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        return ""
    try:
        from PIL import Image
        import pytesseract
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "document.pdf"
            pdf_path.write_bytes(data)
            prefix = str(Path(tmpdir) / "page")
            completed = subprocess.run(
                ["pdftoppm", "-png", str(pdf_path), prefix],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if completed.returncode != 0:
                return ""
            pages = []
            for image_path in sorted(Path(tmpdir).glob("page-*.png")):
                pages.append(pytesseract.image_to_string(Image.open(image_path)))
            return " ".join(pages)
    except Exception:
        return ""


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def ocr_status() -> dict:
    tesseract_installed = bool(shutil.which("tesseract"))
    pdftoppm_installed = bool(shutil.which("pdftoppm"))
    try:
        import pypdf  # noqa: F401

        pypdf_available = True
    except Exception:
        pypdf_available = False
    try:
        import pytesseract  # noqa: F401

        pytesseract_available = True
    except Exception:
        pytesseract_available = False
    try:
        from PIL import Image  # noqa: F401

        pillow_available = True
    except Exception:
        pillow_available = False

    image_ocr_ready = tesseract_installed and pytesseract_available and pillow_available
    scanned_pdf_ocr_ready = image_ocr_ready and pdftoppm_installed
    status = "healthy" if pypdf_available and image_ocr_ready else "degraded"
    if not pypdf_available and not image_ocr_ready:
        status = "down"
    return {
        "status": status,
        "tesseract_installed": tesseract_installed,
        "pdftoppm_installed": pdftoppm_installed,
        "pypdf_available": pypdf_available,
        "pytesseract_available": pytesseract_available,
        "pillow_available": pillow_available,
        "image_ocr_ready": image_ocr_ready,
        "scanned_pdf_ocr_ready": scanned_pdf_ocr_ready,
    }


def evidence_quality(text: str, file_count: int = 0) -> dict:
    cleaned = clean_text(text).lower()
    words = re.findall(r"[a-zA-Z0-9'-]+", cleaned)
    unique_words = set(words)
    repeated_ratio = (len(unique_words) / len(words)) if words else 0
    keyword_hits = sorted(keyword for keyword in EVIDENCE_KEYWORDS if keyword in cleaned)
    has_year_or_date = bool(re.search(r"\b(19\d{2}|20\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", cleaned))
    score = 0
    score += min(len(words) / 80, 0.35)
    score += min(len(unique_words) / 45, 0.2)
    score += min(len(keyword_hits) / 4, 0.25)
    score += 0.1 if has_year_or_date else 0
    score += 0.1 if file_count > 0 else 0
    issues = []
    if len(words) < 18:
        issues.append("The submission is too short for commercial dispute review.")
    if repeated_ratio < 0.45:
        issues.append("The claim appears repetitive or low-information.")
    if not keyword_hits and file_count == 0:
        issues.append("No legal/evidence markers were found. Add documents, dates, registry IDs, payments, ownership, contract, or rental details.")
    return {
        "acceptable": score >= 0.42 and not (len(words) < 18 and file_count == 0),
        "score": round(score, 2),
        "issues": issues,
        "keyword_hits": keyword_hits,
        "has_date": has_year_or_date,
        "word_count": len(words),
        "unique_word_count": len(unique_words),
    }


def structure_text_evidence(text: str, country: str) -> StructuredEvidence:
    lower = text.lower()
    document_type = "land_certificate" if "certificate" in lower or "title" in lower else "civil_document"
    owner_match = re.search(r"owner[:\s]+([A-Za-z .'-]{3,60})", text, re.IGNORECASE)
    registry_match = re.search(r"(REG[-\s]?\d+|registry[:\s]+[A-Z0-9-]+)", text, re.IGNORECASE)
    issues = []
    if "duplicate" in lower:
        issues.append("Potential duplicate document language detected")
    if "registry mismatch" in lower:
        issues.append("Registry mismatch detected")
    if "conflict" in lower:
        issues.append("Conflicting timeline or ownership statement detected")
    return StructuredEvidence(
        document_type=document_type,
        country=country,
        owner=owner_match.group(1).strip() if owner_match else None,
        registry_id=registry_match.group(1).strip() if registry_match else None,
        confidence=0.86 if text.strip() else 0.2,
        issues_detected=issues,
    )


def detect_contradictions(evidence: list[StructuredEvidence]) -> ContradictionReport:
    issues = [issue for item in evidence for issue in item.issues_detected]
    registry_ids = [item.registry_id for item in evidence if item.registry_id]
    if len(registry_ids) != len(set(registry_ids)):
        issues.append("Duplicate registry identifier detected")
    contradiction_detected = bool(issues)
    severity = min(0.95, 0.25 + 0.18 * len(issues)) if contradiction_detected else 0.0
    return ContradictionReport(contradiction_detected=contradiction_detected, severity=severity, issues=issues)


def reconstruct_timeline(text: str) -> list[dict]:
    years = sorted(set(re.findall(r"\b(19\d{2}|20\d{2})\b", text)))
    return [{"year": year, "event": "Referenced in submitted evidence"} for year in years]


def fraud_report(evidence: list[StructuredEvidence], text: str) -> dict:
    lower = text.lower()
    signals = []
    if "forged" in lower or "fake" in lower:
        signals.append("Forgery language present in evidence")
    if any(item.confidence < 0.5 for item in evidence):
        signals.append("Low OCR/structure confidence")
    if any("duplicate" in issue.lower() for item in evidence for issue in item.issues_detected):
        signals.append("Duplicate evidence signal")
    return {"suspicious": bool(signals), "signals": signals, "severity": min(0.95, 0.2 + 0.22 * len(signals)) if signals else 0.0}
