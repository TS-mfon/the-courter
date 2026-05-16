from fastapi import APIRouter

from ..services.retrieval import retrieve_legal_chunks

router = APIRouter()


@router.get("/{country}/{category}")
def retrieve(country: str, category: str) -> dict:
    return {"chunks": retrieve_legal_chunks(country, category)}
