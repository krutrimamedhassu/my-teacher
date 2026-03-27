import os
import json
from typing import List, Optional

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
    status,
)
from pydantic import BaseModel, Field

from app.logger.app_logger import app_logger
from app.core.prompts import PROMPT_REGISTRY
from app.core.data.doc_handler import DocumentHandler, Document
from app.core.response.generative_responder import GenerativeResponder
from app.core.utils.endpoint_utils import extract_json_from_codeblock

router = APIRouter()


# --- Models ---


class FlashcardRequest(BaseModel):
    content: str = Field(
        ...,
        description="Text content or topic to generate flashcards from",
        min_length=2,
    )
    subject_area: str = Field(
        ...,
        description="Subject area of the content",
        min_length=2,
    )
    difficulty_level: str = Field(
        "intermediate",
        description="Difficulty level (e.g. 'beginner', 'advanced')",
    )
    num_cards: int = Field(
        10,
        description="Number of flashcards to generate",
        ge=1,
        le=50,
    )
    context_length: Optional[int] = Field(
        None,
        description="Context length for content processing",
        ge=100,
        le=4000,
    )
    conversation_history: Optional[List[str]] = Field(
        None,
        description="Previous conversation messages for context",
    )


class Flashcard(BaseModel):
    question: str
    answer: str


class FlashcardsResponse(BaseModel):
    flashcards: List[Flashcard]
    subject_area: str
    difficulty_level: str
    total_cards: int


# --- Core Logic Helper ---


async def _generate_flashcards_logic(
    req: FlashcardRequest
) -> FlashcardsResponse:
    """
    Internal helper that:
      1) Expands short content into detailed educational content if needed
      2) Renders the prompt
      3) Calls the LLM
      4) Parses JSON
      5) Validates & returns a FlashcardsResponse
    """
    app_logger.log_info(f"[Flashcards] Starting flashcard generation")
    app_logger.log_info(
        f"[Flashcards] Parameters - cards: {req.num_cards}, "
        f"subject: '{req.subject_area}', level: '{req.difficulty_level}'"
    )
    app_logger.log_debug(f"[Flashcards] Content length: {len(req.content)} characters")
    app_logger.log_debug(f"[Flashcards] Context length setting: {req.context_length}")
    app_logger.log_debug(f"[Flashcards] Conversation history provided: {bool(req.conversation_history)}")

    # Build context from conversation history if provided
    app_logger.log_debug("[Flashcards] Building context from conversation history")
    context_info = ""
    if req.conversation_history:
        app_logger.log_debug(f"[Flashcards] Using last 5 messages from {len(req.conversation_history)} total messages")
        context_info = "\n\nConversation History:\n" + "\n".join(req.conversation_history[-5:])  # Last 5 messages
        app_logger.log_debug(f"[Flashcards] Context info length: {len(context_info)} characters")

    # If content is too short, generate detailed content first
    content = req.content
    app_logger.log_debug(f"[Flashcards] Evaluating content length: {len(content.strip())} characters")
    if len(content.strip()) < 100:  # Expand short topics
        app_logger.log_info(f"[Flashcards] Content too short, expanding topic: {content[:50]}...")
        
        content_expansion_prompt = f"""
Generate comprehensive educational content about "{content}" in the subject area of "{req.subject_area}" at {req.difficulty_level} level.

Include:
- Key concepts and definitions
- Important principles and mechanisms
- Examples and applications
- Common misconceptions to avoid

{context_info}

Write 300-500 words of educational content suitable for creating {req.num_cards} flashcards.
"""
        
        try:
            max_tokens = req.context_length or 800
            app_logger.log_debug(f"[Flashcards] Using max_tokens: {max_tokens} for content expansion")
            app_logger.log_debug("[Flashcards] Creating GenerativeResponder for content expansion")
            async with GenerativeResponder() as responder:
                app_logger.log_debug("[Flashcards] Sending content expansion request to LLM")
                expanded_content = await responder.generate_text(
                    messages=[{"role": "user", "content": content_expansion_prompt}],
                    temperature=0.3,
                )
                content = expanded_content
                app_logger.log_debug(f"[Flashcards] Content expanded from {len(req.content)} to {len(content)} characters")
                app_logger.log_debug(f"[Flashcards] Expanded content preview: {content[:200]}...")
        except Exception as e:
            app_logger.log_error(f"[Flashcards] Failed to expand content: {e}")
            app_logger.log_debug("[Flashcards] Falling back to original content")
            # Fall back to original content
            pass
    else:
        app_logger.log_debug("[Flashcards] Content length sufficient, no expansion needed")
        # For longer content, just append context if available
        if context_info:
            app_logger.log_debug("[Flashcards] Appending conversation context to content")
            content = content + context_info

    app_logger.log_debug("[Flashcards] Getting flashcard generation prompt from registry")
    flashcard_generation_prompt = PROMPT_REGISTRY["flashcard_generation"]

    # Render the prompt with the request parameters
    app_logger.log_debug("[Flashcards] Rendering prompt template")
    rendered_prompt = flashcard_generation_prompt.render(
        num_cards=req.num_cards,
        subject_area=req.subject_area,
        difficulty_level=req.difficulty_level,
        content=content
    )
    app_logger.log_debug(f"[Flashcards] Rendered prompt length: {len(rendered_prompt)} characters")

    app_logger.log_debug(
        f"[Flashcards] Prompt (truncated): {rendered_prompt[:200]}…"
    )

    try:
        # Use async context manager for proper cleanup
        app_logger.log_debug("[Flashcards] Creating GenerativeResponder for flashcard generation")
        async with GenerativeResponder() as responder:
            app_logger.log_debug("[Flashcards] Sending flashcard generation request to LLM")
            raw = await responder.generate_text(
                messages=[{"role": "user", "content": rendered_prompt}],
                temperature=0.3,
            )
            app_logger.log_debug(f"[Flashcards] Received LLM response, length: {len(raw)} characters")
            app_logger.log_debug(f"[Flashcards] Raw LLM response preview: {raw[:200]}...")

        # Clean Markdown code block markers if present
        app_logger.log_debug("[Flashcards] Extracting JSON from LLM response")
        cleaned_raw = extract_json_from_codeblock(raw)
        app_logger.log_debug(f"[Flashcards] Cleaned JSON length: {len(cleaned_raw)} characters")

        app_logger.log_debug("[Flashcards] Parsing JSON response")
        payload = json.loads(cleaned_raw)
        cards = payload.get("flashcards")
        if not isinstance(cards, list) or not cards:
            app_logger.log_error("[Flashcards] LLM returned no flashcards list")
            raise ValueError("LLM returned no flashcards list")

        app_logger.log_debug(f"[Flashcards] Processing {len(cards)} flashcards from LLM")
        flashcards: List[Flashcard] = []
        for idx, c in enumerate(cards):
            if not all(k in c for k in ("question", "answer")):
                app_logger.log_error(f"[Flashcards] Missing keys in flashcard #{idx}: {c!r}")
                raise ValueError(f"Missing keys in flashcard #{idx}: {c!r}")
            flashcard = Flashcard(**c)
            flashcards.append(flashcard)
            app_logger.log_debug(f"[Flashcards] Processed flashcard {idx}: {flashcard.question[:50]}...")

        response = FlashcardsResponse(
            flashcards=flashcards,
            subject_area=req.subject_area,
            difficulty_level=req.difficulty_level,
            total_cards=len(flashcards),
        )

        app_logger.log_info(f"[Flashcards] Successfully generated {len(flashcards)} flashcards")
        return response

    except json.JSONDecodeError as e:
        app_logger.log_error(f"[Flashcards] JSON parse error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to parse LLM JSON response",
        )
    except ValueError as e:
        app_logger.log_error(f"[Flashcards] Value error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM error: {e}",
        )
    except HTTPException:
        # Already logged; re-raise
        raise
    except Exception as e:
        app_logger.log_error(f"[Flashcards] Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error generating flashcards",
        )


# --- Routes ---


@router.post(
    "/",
    response_model=FlashcardsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Flashcards from Text",
    description="Create question/answer flashcards from raw text.",
)
async def generate_flashcards(request: FlashcardRequest) -> FlashcardsResponse:
    """
    Accepts a JSON body with `content`, `subject_area`, `difficulty_level`,
    and `num_cards`, then returns a list of generated flashcards.
    """
    app_logger.log_info("[Flashcards] Text-based flashcard generation requested")
    app_logger.log_debug(f"[Flashcards] Request content preview: {request.content[:100]}...")
    return await _generate_flashcards_logic(request)


@router.post(
    "/from-file",
    response_model=FlashcardsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Flashcards from File",
    description="Upload a document file (PDF, DOCX, etc.) and generate flashcards.",
)
async def generate_flashcards_from_file(
    file: UploadFile = File(...),
    subject_area: str = Form(...),
    difficulty_level: str = Form("intermediate"),
    num_cards: int = Form(10),
    context_length: Optional[int] = Form(None),
    conversation_history: Optional[str] = Form(None),
) -> FlashcardsResponse:
    """
    Accepts an uploaded file, extracts its text content, and generates
    flashcards according to the provided metadata.
    """
    app_logger.log_info(f"[Flashcards] File-based flashcard generation requested for: {file.filename}")
    app_logger.log_debug(f"[Flashcards] File details - size: {file.size if hasattr(file, 'size') else 'unknown'}, content_type: {file.content_type}")
    app_logger.log_debug(f"[Flashcards] Parameters - subject: {subject_area}, level: {difficulty_level}, cards: {num_cards}")

    temp_path = f"/tmp/flashcards_{os.getpid()}_{file.filename}"
    app_logger.log_debug(f"[Flashcards] Using temporary file path: {temp_path}")
    try:
        # Save the uploaded file to disk
        app_logger.log_debug("[Flashcards] Reading uploaded file content")
        contents = await file.read()
        app_logger.log_debug(f"[Flashcards] File content read, size: {len(contents)} bytes")

        app_logger.log_debug(f"[Flashcards] Saving file to temporary path: {temp_path}")
        with open(temp_path, "wb") as f:
            f.write(contents)
        app_logger.log_debug("[Flashcards] File saved successfully")

        # Extract text from the document
        app_logger.log_debug("[Flashcards] Parsing document to extract text")
        document: Document = DocumentHandler.parse_document(temp_path)
        app_logger.log_debug(f"[Flashcards] Document parsed, content length: {len(document.content)} characters")
        app_logger.log_debug(f"[Flashcards] Document content preview: {document.content[:200]}...")

        # Parse conversation history if provided
        parsed_conversation_history = None
        if conversation_history:
            app_logger.log_debug("[Flashcards] Parsing conversation history")
            try:
                parsed_conversation_history = json.loads(conversation_history)
                app_logger.log_debug(f"[Flashcards] Parsed conversation history as JSON with {len(parsed_conversation_history)} items")
            except json.JSONDecodeError:
                app_logger.log_debug("[Flashcards] Treating conversation history as single string")
                # Treat as single string if not valid JSON
                parsed_conversation_history = [conversation_history]

        # Build a FlashcardRequest and delegate to the core logic
        app_logger.log_debug("[Flashcards] Building FlashcardRequest from file content")
        req = FlashcardRequest(
            content=document.content,
            subject_area=subject_area,
            difficulty_level=difficulty_level,
            num_cards=num_cards,
            context_length=context_length,
            conversation_history=parsed_conversation_history,
        )
        app_logger.log_debug("[Flashcards] Delegating to core generation logic")
        return await _generate_flashcards_logic(req)

    except HTTPException:
        # Already logged in helper or framework
        raise
    except Exception as e:
        app_logger.log_error(f"[Flashcards] File-based error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate flashcards from file",
        )
    finally:
        # Clean up temporary file
        app_logger.log_debug(f"[Flashcards] Cleaning up temporary file: {temp_path}")
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                app_logger.log_debug("[Flashcards] Temporary file deleted successfully")
            else:
                app_logger.log_debug("[Flashcards] Temporary file does not exist, no cleanup needed")
        except Exception as e:
            app_logger.log_warning(f"[Flashcards] Could not delete {temp_path}: {e}")