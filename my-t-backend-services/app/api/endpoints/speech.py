from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from app.core.auth.optional_auth import get_user_with_usage_tracking, create_limit_exceeded_response
from app.core.clients import openai_client, async_openai_client
from app.core.config import settings
import os
import re
from tempfile import NamedTemporaryFile
from typing import AsyncGenerator
from app.logger.app_logger import app_logger

router = APIRouter()


def split_text_for_tts(text: str, max_chars: int = 500) -> list[str]:
    """
    Split text into chunks suitable for TTS streaming.
    Splits on sentence boundaries to maintain natural speech flow.

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    # Split on sentence boundaries (., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # If adding this sentence would exceed max_chars, save current chunk
        if len(current_chunk) + len(sentence) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence

    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


class TTSRequest(BaseModel):
    text: str
    voice: str = None  # Will use settings.TTS_VOICE if not provided


@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    request: Request = None
):
    """
    Speech-to-Text endpoint using OpenAI Whisper API
    Accepts audio file and returns transcribed text
    """
    user_id, identifier, usage_info, _ = await get_user_with_usage_tracking(request, "speech_stt")
    if not usage_info.get("allowed", True):
        raise HTTPException(status_code=429, detail=create_limit_exceeded_response(usage_info))

    app_logger.log_info(f"[Speech] STT request from identifier={identifier}")

    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

        # Save uploaded file temporarily
        with NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        app_logger.log_info(f"[Speech] Audio file saved temporarily: {temp_file_path}")

        # Transcribe using OpenAI Whisper
        with open(temp_file_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        # Clean up temp file
        os.unlink(temp_file_path)
        app_logger.log_info(f"[Speech] Transcription completed successfully")

        return {
            "text": transcript,
            "status": "success"
        }

    except Exception as e:
        app_logger.log_error(f"[Speech] Error in STT: {str(e)}")
        # Clean up temp file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/tts")
async def text_to_speech(
    tts_request: TTSRequest,
    request: Request = None
):
    """
    Text-to-Speech endpoint using OpenAI TTS API
    Accepts text and returns audio file
    """
    user_id, identifier, usage_info, _ = await get_user_with_usage_tracking(request, "speech_tts")
    if not usage_info.get("allowed", True):
        raise HTTPException(status_code=429, detail=create_limit_exceeded_response(usage_info))

    app_logger.log_info(f"[Speech] TTS request from identifier={identifier}")

    try:
        # Validate text length (OpenAI has a 4096 character limit)
        if len(tts_request.text) > 4096:
            raise HTTPException(status_code=400, detail="Text too long. Maximum 4096 characters.")

        if not tts_request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty.")

        # Use voice from request or fall back to environment setting
        final_voice = tts_request.voice or settings.TTS_VOICE
        final_model = settings.TTS_MODEL

        app_logger.log_info(f"[Speech] Generating TTS with model: {final_model}, voice: {final_voice}")

        # Generate speech using OpenAI TTS
        response = openai_client.audio.speech.create(
            model=final_model,
            voice=final_voice,
            input=tts_request.text
        )

        app_logger.log_info(f"[Speech] TTS completed successfully")

        # Return audio as response
        return Response(
            content=response.content,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )

    except Exception as e:
        app_logger.log_error(f"[Speech] Error in TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


@router.post("/tts/stream")
async def text_to_speech_streaming(
    tts_request: TTSRequest,
    request: Request = None
):
    """
    Streaming Text-to-Speech endpoint for faster perceived response time.
    Splits long text into chunks and streams audio progressively.
    """
    user_id, identifier, usage_info, _ = await get_user_with_usage_tracking(request, "speech_tts_stream")
    if not usage_info.get("allowed", True):
        raise HTTPException(status_code=429, detail=create_limit_exceeded_response(usage_info))

    app_logger.log_info(f"[Speech] Streaming TTS request from identifier={identifier}, text length: {len(tts_request.text)}")

    try:
        # Validate text length
        if len(tts_request.text) > 4096:
            raise HTTPException(status_code=400, detail="Text too long. Maximum 4096 characters.")

        if not tts_request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty.")

        # Use voice from request or fall back to environment setting
        final_voice = tts_request.voice or settings.TTS_VOICE
        final_model = settings.TTS_MODEL

        # For short text (< 500 chars), use regular non-streaming TTS
        if len(tts_request.text) <= 500:
            app_logger.log_info(f"[Speech] Text is short, using regular TTS")
            response = openai_client.audio.speech.create(
                model=final_model,
                voice=final_voice,
                input=tts_request.text
            )
            return Response(
                content=response.content,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "attachment; filename=speech.mp3"
                }
            )

        # For long text, split into chunks and stream
        app_logger.log_info(f"[Speech] Text is long, splitting into chunks for streaming")
        chunks = split_text_for_tts(tts_request.text, max_chars=500)
        app_logger.log_info(f"[Speech] Split text into {len(chunks)} chunks")

        async def generate_audio_stream() -> AsyncGenerator[bytes, None]:
            """Generate audio chunks progressively using async API calls."""
            for i, chunk in enumerate(chunks):
                app_logger.log_debug(f"[Speech] Generating audio for chunk {i+1}/{len(chunks)}")
                try:
                    # Generate audio for this chunk using async client
                    response = await async_openai_client.audio.speech.create(
                        model=final_model,
                        voice=final_voice,
                        input=chunk
                    )
                    yield response.content
                    app_logger.log_debug(f"[Speech] Chunk {i+1}/{len(chunks)} completed")
                except Exception as e:
                    app_logger.log_error(f"[Speech] Error generating chunk {i+1}: {str(e)}")
                    raise

            app_logger.log_info(f"[Speech] Streaming TTS completed successfully")

        return StreamingResponse(
            generate_audio_stream(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
                "X-Chunk-Count": str(len(chunks))
            }
        )

    except Exception as e:
        app_logger.log_error(f"[Speech] Error in streaming TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text-to-speech streaming failed: {str(e)}")
