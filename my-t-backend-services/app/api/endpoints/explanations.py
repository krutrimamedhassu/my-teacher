# app/api/explanation.py

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.logger.app_logger import app_logger
from app.core.prompts import get_persona_prompt
from app.core.response.generative_responder import GenerativeResponder

router = APIRouter()

ALLOWED_PERSONAS = [
    "expert_professor",
    "relatable_tutor",
    "storyteller",
    "visual_explainer",
    "exam_coach",
    "celebrity",
]


class ExplanationRequest(BaseModel):
    concept: str = Field(..., description="Concept to explain")
    persona: str = Field(..., description="Persona to use for explanation")
    subject_area: str = Field(..., description="Subject area of the concept")
    student_level: str = Field(
        "intermediate", description="Student's knowledge level"
    )
    context: Optional[str] = Field(
        None, description="Additional context for the explanation"
    )
    celebrity_name: Optional[str] = Field(
        None, description="Celebrity name (required if persona='celebrity')"
    )


class ExplanationResponse(BaseModel):
    concept: str = Field(..., description="The concept that was explained")
    explanation: str = Field(..., description="The generated explanation")
    persona: str = Field(..., description="The persona used for the explanation")
    subject_area: str = Field(..., description="The subject area")
    student_level: str = Field(..., description="The student level targeted")


@router.post(
    "/explain",
    response_model=ExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Personalized Explanation",
    description="Generate an explanation of a concept using a selected persona.",
)
async def generate_explanation(
    req: ExplanationRequest,
) -> ExplanationResponse:
    app_logger.log_info(f"[Explanations] Starting explanation generation")
    app_logger.log_info(
        f"[Explanations] Request parameters - concept: {req.concept!r}, persona: {req.persona!r}, "
        f"subject_area: {req.subject_area!r}, level: {req.student_level!r}"
    )
    app_logger.log_debug(f"[Explanations] Context provided: {bool(req.context)}")
    app_logger.log_debug(f"[Explanations] Celebrity name: {req.celebrity_name}")

    # 1) Validate persona
    app_logger.log_debug(f"[Explanations] Validating persona: {req.persona}")
    if req.persona not in ALLOWED_PERSONAS:
        app_logger.log_warning(f"[Explanations] Invalid persona requested: {req.persona}")
        app_logger.log_debug(f"[Explanations] Allowed personas: {ALLOWED_PERSONAS}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid persona. Choose from: {', '.join(ALLOWED_PERSONAS)}",
        )

    if req.persona == "celebrity" and not req.celebrity_name:
        app_logger.log_warning("[Explanations] Celebrity persona requested but no celebrity name provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`celebrity_name` is required when persona='celebrity'.",
        )

    app_logger.log_debug(f"[Explanations] Persona validation passed for: {req.persona}")

    # 2) Build prompt variables
    app_logger.log_debug("[Explanations] Building prompt variables")
    prompt_kwargs = {
        "concept": req.concept,
        "subject_area": req.subject_area,
        "student_level": req.student_level,
        "context": req.context or "No additional context provided.",
    }
    if req.persona == "celebrity":
        prompt_kwargs["celebrity_name"] = req.celebrity_name  # type: ignore
        app_logger.log_debug(f"[Explanations] Added celebrity name to prompt: {req.celebrity_name}")

    app_logger.log_debug(f"[Explanations] Prompt variables prepared: {list(prompt_kwargs.keys())}")

    # 3) Render the persona prompt
    app_logger.log_debug(f"[Explanations] Rendering persona prompt for: {req.persona}")
    prompt_text = get_persona_prompt(req.persona, **prompt_kwargs)
    app_logger.log_debug(f"[Explanations] Prompt generated, length: {len(prompt_text)} characters")
    app_logger.log_debug(f"[Explanations] Prompt preview: {prompt_text[:200]}…")

    # 4) Call the LLM with proper cleanup
    try:
        app_logger.log_debug("[Explanations] Creating GenerativeResponder")
        async with GenerativeResponder() as responder:
            app_logger.log_debug("[Explanations] Sending request to LLM")
            explanation_raw = await responder.generate_text(
                messages=[{"role": "user", "content": prompt_text}],
            )
            explanation = explanation_raw.strip()
            app_logger.log_debug(f"[Explanations] Received LLM response, length: {len(explanation)} characters")
    except HTTPException:
        # pass through our own 4xx errors
        app_logger.log_warning("[Explanations] HTTPException caught, re-raising")
        raise
    except Exception as e:
        app_logger.log_error(f"[Explanations] LLM call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation.",
        )

    # 5) Return structured response
    response = ExplanationResponse(
        concept=req.concept,
        explanation=explanation,
        persona=req.persona,
        subject_area=req.subject_area,
        student_level=req.student_level,
    )

    app_logger.log_info(f"[Explanations] Successfully generated explanation for concept: {req.concept}")
    return response


@router.get(
    "/personas",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Get Available Personas",
    description="List all supported explanation personas and their descriptions.",
)
async def list_personas() -> Dict[str, str]:
    app_logger.log_info("[Explanations] Personas list requested")
    app_logger.log_debug(f"[Explanations] Available personas count: {len(ALLOWED_PERSONAS)}")

    personas_data = {
        "expert_professor": (
            "Academic depth and precision, scholarly language and references."
        ),
        "relatable_tutor": (
            "Friendly, conversational tone with everyday examples and analogies."
        ),
        "storyteller": "Engaging narratives, characters, and plot-driven explanations.",
        "visual_explainer": (
            "Vivid visual descriptions, spatial relationships, and mental imagery."
        ),
        "exam_coach": (
            "Focus on exam prep: key points, common test questions, and tips."
        ),
        "celebrity": (
            "In the style of a specified celebrity or character, "
            "using their speech patterns."
        ),
    }

    app_logger.log_debug(f"[Explanations] Returning {len(personas_data)} persona descriptions")
    app_logger.log_info("[Explanations] Personas list served successfully")
    return personas_data