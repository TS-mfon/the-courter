from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..services.evidence import extract_text, structure_text_evidence

router = APIRouter()


class EvidenceTextRequest(BaseModel):
    text: str
    country: str


@router.post("/structure")
def structure(payload: EvidenceTextRequest) -> dict:
    return structure_text_evidence(payload.text, payload.country).model_dump()


@router.post("/process")
async def process(case_id: str = Form("draft"), username: str = Form("anonymous"), files: list[UploadFile] = File(...)) -> dict:
    extracted = []
    for file in files:
        try:
            extracted.append(await extract_text(file, case_id, username))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"files": extracted}
