# app/api/key_concepts.py

import json
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.logger.app_logger import app_logger
from app.core.prompts import KEY_CONCEPT_PROMPT
from app.core.response.generative_responder import GenerativeResponder
from app.core.utils.endpoint_utils import extract_json_from_codeblock

router = APIRouter()


class KeyConceptRequest(BaseModel):
    content: str = Field(..., description="Content to extract key concepts from")
    subject_area: str = Field(..., description="Subject area of the content")


class KeyConcept(BaseModel):
    type: str
    content: str
    description: Optional[str] = None


class KeyConceptResponse(BaseModel):
    concepts: List[KeyConcept]
    subject_area: str
    total_concepts: int


def _flatten_response(data: Dict[str, Any]) -> List[KeyConcept]:
    """
    Turn the raw JSON dict from the LLM into a flat list of KeyConcept models.
    """
    items: List[KeyConcept] = []

    # concepts
    for c in data.get("concepts", []):
        items.append(KeyConcept(type="concept", content=c))

    # definitions
    for d in data.get("definitions", []):
        items.append(
            KeyConcept(
                type="definition",
                content=d["term"],
                description=d.get("definition"),
            )
        )

    # formulas
    for f in data.get("formulas", []):
        items.append(KeyConcept(type="formula", content=f))

    # takeaways
    for t in data.get("takeaways", []):
        items.append(KeyConcept(type="takeaway", content=t))

    # relationships (new: source/target, fallback: from/to)
    for r in data.get("relationships", []):
        source = r.get("source") or r.get("from")
        target = r.get("target") or r.get("to")
        if not source or not target:
            app_logger.log_error(f"Skipping malformed relationship entry: {r}")
            continue
        items.append(
            KeyConcept(
                type="relationship",
                content=f"{source} → {target}",
                description=r.get("description"),
            )
        )

    return items


@router.post(
    "/extract-key-concepts",
    response_model=KeyConceptResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Key Concepts",
    description="Use the LLM to pull out concepts, definitions, formulas, etc.",
)
async def extract_key_concepts(req: KeyConceptRequest) -> KeyConceptResponse:
    app_logger.log_info(f"[KeyConcepts] Extracting for subject_area={req.subject_area!r}")

    # 1) Render the prompt
    prompt = KEY_CONCEPT_PROMPT.render(
        content=req.content, subject_area=req.subject_area
    )
    app_logger.log_debug(f"[KeyConcepts] Prompt: {prompt[:200]}…")

    # 2) Call the LLM with proper cleanup
    try:
        async with GenerativeResponder() as llm_client:
            raw_text = await llm_client.generate_text(
                messages=[{"role": "user", "content": prompt}],
            )
    except Exception as e:
        app_logger.exception(f"[KeyConcepts] LLM call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM service error when extracting key concepts.",
        )

    # 3) Parse JSON - handle markdown code blocks
    try:
        # Clean Markdown code block markers if present
        cleaned_raw = extract_json_from_codeblock(raw_text)
        app_logger.log_debug(f"[KeyConcepts] Extracted JSON: {cleaned_raw[:200]}...")
        payload: Dict[str, Any] = json.loads(cleaned_raw)
    except json.JSONDecodeError as e:
        app_logger.log_error(f"[KeyConcepts] JSON parse error: {e}")
        app_logger.log_debug(f"[KeyConcepts] Raw LLM response: {raw_text[:500]}...")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received malformed JSON from LLM.",
        )

    # 4) Flatten & validate
    concepts = _flatten_response(payload)
    if not concepts:
        app_logger.log_warning("[KeyConcepts] No concepts extracted.")
        # It's still a 200, but returns an empty list
    return KeyConceptResponse(
        concepts=concepts,
        subject_area=req.subject_area,
        total_concepts=len(concepts),
    )