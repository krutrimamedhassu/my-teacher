# app/api/endpoints/problems.py

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.logger.app_logger import app_logger
from app.core.prompts import MCQ_PROMPT
from app.core.response.generative_responder import GenerativeResponder
from app.core.utils.endpoint_utils import extract_json_from_codeblock

router = APIRouter()


class MCQ(BaseModel):
    question: str
    choices: Dict[str, str]  # keys: 'A', 'B', 'C', 'D'
    correct_option: str      # e.g., 'A', 'B', 'C', 'D'
    answer: str
    solution: str


class MCQRequest(BaseModel):
    content: str = Field(..., description="Educational content to base MCQs on")
    subject_area: str = Field(..., description="Subject area of the content")
    difficulty_level: str = Field("intermediate", description="Difficulty level")
    num_mcqs: int = Field(3, description="Number of MCQs to generate")


class MCQResponse(BaseModel):
    mcqs: List[Dict[str, Any]] = Field(..., description="Generated MCQs")
    subject_area: str = Field(..., description="Subject area")
    difficulty_level: str = Field(..., description="Difficulty level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


@router.post(
    "/",
    response_model=MCQResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Multiple Choice Questions",
    description="Generate multiple choice questions based on educational content."
)
async def generate_mcqs(request: MCQRequest) -> MCQResponse:
    app_logger.log_info(
        f"[MCQ] Generating {request.num_mcqs} "
        f"{request.difficulty_level} MCQs for {request.subject_area!r}"
    )

    # 1) Render the prompt
    prompt = MCQ_PROMPT.render(
        content=request.content,
        subject_area=request.subject_area,
        difficulty_level=request.difficulty_level,
        num_mcqs=request.num_mcqs,
    )
    app_logger.log_debug(f"[MCQ] Prompt (trunc): {prompt[:200]}…")

    # 2) Call the LLM with proper cleanup
    try:
        async with GenerativeResponder() as responder:
            raw = await responder.generate_text(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            app_logger.log_debug(f"[MCQ] Raw LLM output: {raw!r}")
    except Exception as e:
        app_logger.log_error(f"[MCQ] LLM call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM service error when generating MCQs."
        )

    # 3) Parse JSON - handle markdown code blocks
    try:
        cleaned_raw = extract_json_from_codeblock(raw)
        app_logger.log_debug(f"[MCQ] Extracted JSON: {cleaned_raw[:200]}...")
        payload: Dict[str, Any] = json.loads(cleaned_raw)
    except json.JSONDecodeError as e:
        app_logger.log_error(f"[MCQ] JSON parse error: {e}")
        app_logger.log_debug(f"[MCQ] Raw LLM response: {raw[:500]}...")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received malformed JSON from LLM."
        )

    # 4) Validate payload
    mcqs = payload.get("mcqs")
    if not isinstance(mcqs, list):
        app_logger.log_error(f"Expected 'mcqs' list, got {type(mcqs)}")
        app_logger.log_debug(f"Raw LLM response: {raw}")
        raise HTTPException(status_code=502, detail="LLM response missing 'mcqs' list.")

    # 5) Return structured response
    return MCQResponse(
        mcqs=mcqs,
        subject_area=request.subject_area,
        difficulty_level=request.difficulty_level,
        metadata={
            "num_mcqs": len(mcqs),
            "content_length": len(request.content),
        },
    )