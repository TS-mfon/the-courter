from __future__ import annotations

import json
from courter_shared.paths import resolve_data_dir


def retrieve_legal_chunks(country: str, category: str, limit: int = 5) -> list[dict]:
    category_path = "civil_arbitration" if category == "civil_arbitration" else category
    if category_path == "civil_arbitration":
        category_path = "contract"
    path = resolve_data_dir("laws") / country.lower() / category_path.lower() / f"{category_path.lower()}_chunks.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        chunks = json.load(handle)
    ranked = sorted(chunks, key=lambda chunk: chunk.get("importance", 0), reverse=True)[:limit]
    for chunk in ranked:
        chunk.setdefault(
            "judge_relevance",
            {
                "Justice Veritas": 0.91 if "ownership" in " ".join(chunk.get("keywords", [])).lower() else 0.74,
                "Justice Harmony": 0.72,
                "Justice Equity": 0.8,
                "Justice Ratio": 0.93,
            },
        )
    return ranked
