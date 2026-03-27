import json
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.response.generative_responder import GenerativeResponder
from app.core.prompts import PROMPT_REGISTRY
from app.core.utils.endpoint_utils import extract_json_from_codeblock
from app.core.config import settings
from app.logger.app_logger import app_logger

router = APIRouter(
    prefix="/topic-breakdown",
    tags=["breakdowns"]
)

# --- Data Models ---
class BreakdownRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=2,
        description="The text/content to be broken down into topics.",
    )
    subject_area: str = Field(
        ...,
        min_length=2,
        description="The subject area or domain (e.g. 'biology').",
    )

class TopicItem(BaseModel):
    id: str    # e.g. "1", "1.1"
    title: str
    summary: str

class BreakdownResponse(BaseModel):
    subject_area: str
    topics: List[TopicItem]


@router.post(
    "/",
    response_model=BreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Break Down Content by Topic",
    description=(
        "Analyze the provided content and return a structured outline "
        "of topics and subtopics as JSON."
    ),
)
async def break_down_content(request: BreakdownRequest) -> BreakdownResponse:
    app_logger.log_info(f"[Breakdown] Starting topic breakdown for subject_area: {request.subject_area}")
    app_logger.log_debug(f"[Breakdown] Content length: {len(request.content)} characters")
    app_logger.log_debug(f"[Breakdown] Request content preview: {request.content[:100]}...")

    # If content is too short, expand it with context about the subject area
    content = request.content
    if len(content.strip()) < 50:  # Expand very short topics
        app_logger.log_info(f"[Breakdown] Content too short, expanding topic: {content}")

        content_expansion_prompt = f"""
Generate comprehensive educational content about "{content}" in the subject area of "{request.subject_area}".

Include:
- Key concepts and main topics typically covered
- Important subtopics and areas of focus
- Core principles and fundamental ideas
- Common applications or examples
- Standard curriculum structure for this subject

Write 200-400 words of educational content suitable for creating a detailed topic breakdown.
"""

        try:
            app_logger.log_debug("[Breakdown] Creating GenerativeResponder for content expansion")
            async with GenerativeResponder() as responder:
                app_logger.log_debug("[Breakdown] Generating expanded content")
                expanded_content = await responder.generate_text(
                    messages=[{"role": "user", "content": content_expansion_prompt}],
                    model="gpt-4o",
                    max_tokens=settings.MAX_TOKENS_GEN_TEXT,
                    temperature=0.3,
                )
                content = expanded_content
                app_logger.log_debug(f"[Breakdown] Content expanded successfully. New length: {len(content)}")
                app_logger.log_debug(f"[Breakdown] Expanded content preview: {content[:200]}...")
        except Exception as e:
            app_logger.log_error(f"[Breakdown] Failed to expand content: {e}")
            app_logger.log_debug("[Breakdown] Falling back to original content")
            # Fall back to original content
            pass

    app_logger.log_debug("[Breakdown] Getting topic breakdown prompt from registry")
    prompt = PROMPT_REGISTRY["topic_breakdown"]

    app_logger.log_debug("[Breakdown] Rendering prompt template")
    prompt_text = prompt.render(
        content=content,
        subject_area=request.subject_area,
    )
    app_logger.log_debug(f"[Breakdown] Rendered prompt length: {len(prompt_text)} characters")
    app_logger.log_debug(f"[Breakdown] Prompt preview: {prompt_text[:200]}…")

    messages = [{"role": "user", "content": prompt_text}]

    try:
        # Use async context manager for proper cleanup
        app_logger.log_debug("[Breakdown] Creating GenerativeResponder for topic breakdown")
        async with GenerativeResponder() as responder:
            app_logger.log_debug("[Breakdown] Sending request to LLM")
            raw = await responder.generate_text(
                messages=messages,
                temperature=0.3,
            )
            app_logger.log_debug(f"[Breakdown] Received LLM response, length: {len(raw)} characters")
            app_logger.log_debug(f"[Breakdown] Raw LLM response preview: {raw[:200]}...")

        # Clean up the raw response to extract JSON
        app_logger.log_debug("[Breakdown] Extracting JSON from LLM response")
        cleaned_raw = extract_json_from_codeblock(raw)
        app_logger.log_debug(f"[Breakdown] Cleaned JSON length: {len(cleaned_raw)} characters")

        app_logger.log_debug("[Breakdown] Parsing JSON response")
        payload = json.loads(cleaned_raw)
        topics_raw = payload.get("topics")

        if not isinstance(topics_raw, list) or not topics_raw:
            app_logger.log_error(f"[Breakdown] LLM returned invalid topics payload: {payload!r}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM did not return a valid topics list.",
            )

        app_logger.log_debug(f"[Breakdown] Processing {len(topics_raw)} topics from LLM response")
        topics: List[TopicItem] = []
        for idx, t in enumerate(topics_raw):
            try:
                topic_item = TopicItem(**t)
                topics.append(topic_item)
                app_logger.log_debug(f"[Breakdown] Successfully processed topic {idx}: {topic_item.title}")
            except Exception as e:
                app_logger.log_error(
                    f"[Breakdown] Invalid topic schema at index {idx}: {t!r} — {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Malformed topic structure returned by LLM.",
                )

        response = BreakdownResponse(
            subject_area=request.subject_area,
            topics=topics,
        )

        app_logger.log_info(f"[Breakdown] Successfully created breakdown with {len(topics)} topics for subject: {request.subject_area}")
        return response

    except json.JSONDecodeError as e:
        app_logger.log_error(f"[Breakdown] JSON parse error: {e}")
        app_logger.log_debug(f"[Breakdown] Failed to parse JSON: {cleaned_raw[:500]}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to parse LLM JSON response.",
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Breakdown] Unexpected error during topic breakdown: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during topic breakdown.",
        )