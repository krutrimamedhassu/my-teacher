# app/api/endpoints/visuals.py

import json
import re
from string import Template
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from enum import Enum, unique

from app.logger.app_logger import app_logger
from app.core.prompts import PROMPT_REGISTRY
from app.core.response.generative_responder import GenerativeResponder
from app.core.utils.endpoint_utils import extract_json_from_codeblock

router = APIRouter()


@unique
class VisualType(str, Enum):
    FLOWCHART = "flowchart"


class VisualRequest(BaseModel):
    content: str = Field(..., description="Text content to visualize")
    subject_area: str = Field(..., description="Subject area of the content")
    visual_type: VisualType = Field(
        VisualType.FLOWCHART, description="Type of visual to generate (flowchart only)"
    )
    focus: Optional[str] = Field(None, description="Specific focus area for the visual")


class VisualResponse(BaseModel):
    visual_type: str = Field(..., description="Type of visual generated")
    title: str = Field(..., description="Title of the visual")
    description: str = Field(..., description="Description of the visual")
    elements: List[Dict[str, Any]] = Field(
        ..., description="Visual elements (nodes, edges, etc.)"
    )
    layout: Optional[Dict[str, Any]] = Field(None, description="Layout information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


def _enum_to_value(obj: Any) -> Any:
    """Coerce Enum instances to their .value recursively inside dicts/lists."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _enum_to_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_enum_to_value(v) for v in obj]
    return obj


def _safe_render_prompt(prompt_tpl, **kwargs) -> str:
    """
    Try the prompt's .render(**kwargs) first. If it fails due to {} braces in JSON,
    fall back to a brace-safe renderer by converting {visual_type}/{subject_area}/{content}
    to $visual_type/$subject_area/$content and using string.Template.
    """
    # Always pass only primitive/str values to the renderer
    kwargs = _enum_to_value(kwargs)

    # 1) Primary path: whatever PersonaPrompt.render does
    try:
        return prompt_tpl.render(**kwargs)
    except KeyError as e:
        app_logger.log_warning(f"[Visuals] Primary render failed (KeyError: {e}). Falling back to Template renderer.")
    except Exception as e:
        app_logger.log_warning(f"[Visuals] Primary render failed ({type(e).__name__}: {e}). Falling back to Template renderer.")

    # 2) Fallback path: use the raw template string safely
    tpl_src = getattr(prompt_tpl, "template", None)
    if not isinstance(tpl_src, str) or not tpl_src:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Visual prompt template not configured properly.",
        )

    # Replace ONLY our three placeholders, leave all JSON braces intact
    def repl(m: re.Match) -> str:
        name = m.group(1)
        return f"${name}"

    safe_tpl = re.sub(r"\{(visual_type|subject_area|content)\}", repl, tpl_src)

    try:
        return Template(safe_tpl).safe_substitute(**kwargs)
    except Exception as e:
        app_logger.log_error(f"[Visuals] Template fallback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to render visual prompt.",
        )


@router.post(
    "/",
    response_model=VisualResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a Flowchart",
    description="Produce structured JSON for a flowchart based on text content.",
)
async def generate_visual(request: VisualRequest) -> VisualResponse:
    app_logger.log_info(f"[Visuals] Generating flowchart for subject_area={request.subject_area!r}")

    # 1) Load prompt template
    try:
        prompt_tpl = PROMPT_REGISTRY["visuals_generator"]
    except KeyError:
        app_logger.log_error("[Visuals] VISUALS_PROMPT not found in registry")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Visual prompt template not configured",
        )

    # 2) Render prompt (robust to JSON braces)
    prompt = _safe_render_prompt(
        prompt_tpl,
        visual_type=request.visual_type.value,  # ensure "flowchart"
        subject_area=request.subject_area,
        content=request.content,
    )
    app_logger.log_debug(f"[Visuals] Rendered prompt (first 500 chars): {prompt[:500]}…")

    # 3) Call LLM
    try:
        async with GenerativeResponder() as responder:
            raw_text = await responder.generate_text(messages=[{"role": "user", "content": prompt}])
            app_logger.log_debug(f"[Visuals] Raw LLM output (first 800 chars): {raw_text[:800]!r}")
    except Exception as e:
        app_logger.log_error(f"[Visuals] LLM generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM service error when generating flowchart.",
        )

    # 4) Parse JSON (strip ```json fences etc.)
    try:
        cleaned_raw = extract_json_from_codeblock(raw_text)
        app_logger.log_debug(f"[Visuals] Extracted JSON (first 300 chars): {cleaned_raw[:300]}...")
        payload: Dict[str, Any] = json.loads(cleaned_raw)
    except json.JSONDecodeError as e:
        app_logger.log_error(f"[Visuals] JSON parse error: {e}")
        app_logger.log_debug(f"[Visuals] Raw LLM response head: {raw_text[:600]}...")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received malformed JSON from LLM.",
        )

    # 5) Preserve extras into metadata while validating schema
    #    (VisualResponse will ignore extras by default, but we keep them explicitly.)
    try:
        allowed = {"visual_type", "title", "description", "elements", "layout", "metadata"}
        extras = {k: v for k, v in payload.items() if k not in allowed}
        if extras:
            meta = dict(payload.get("metadata") or {})
            meta["extras"] = {**(meta.get("extras") or {}), **extras}
            payload["metadata"] = meta
            # Remove extras from top-level to avoid confusion
            for k in list(extras.keys()):
                payload.pop(k, None)

        # Ensure required fields exist / types are right
        model = VisualResponse.parse_obj(payload)
        return model
    except ValidationError as e:
        app_logger.log_error(f"[Visuals] Response schema validation failed: {e}")
        app_logger.log_debug(f"[Visuals] Payload that failed: {json.dumps(payload, ensure_ascii=False)[:800]}...")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned JSON in an unexpected format.",
        )
