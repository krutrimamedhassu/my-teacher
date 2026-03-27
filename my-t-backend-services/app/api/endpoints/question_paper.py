from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json

from app.logger.app_logger import app_logger
from app.core.data.document_store import document_store
from app.core.response.generative_responder import GenerativeResponder
from app.core.utils.endpoint_utils import extract_json_from_codeblock
from app.core.prompts import PROMPT_REGISTRY

router = APIRouter()


class QARequest(BaseModel):
    document_id: Optional[str] = Field(None, description="ID of the document to generate Q&A pairs from")
    content: Optional[str] = Field(None, description="Direct content to generate Q&A pairs from")
    context: Optional[str] = Field(None, description="Additional context for QA generation")
    num_pairs: int = Field(5, description="Number of Q&A pairs to generate")

class QAPair(BaseModel):
    question: str
    answer: str

class QAResponse(BaseModel):
    document_id: Optional[str] = None
    content_preview: Optional[str] = None
    qa_pairs: List[QAPair]

@router.post(
    "/",
    response_model=QAResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Q&A Pairs About Document or Content",
    description="Generate a list of Q&A pairs from a document or direct content using the LLM."
)
async def qa_endpoint(request: QARequest) -> QAResponse:
    app_logger.log_info(f"QA endpoint called for document: {request.document_id} or content length: {len(request.content) if request.content else 0}")
    
    try:
        content = None
        document_id = None
        
        # Handle document-based request
        if request.document_id:
            document_id = request.document_id
            content = await document_store.get_document_content(request.document_id)
            if not content:
                raise HTTPException(status_code=404, detail="Document not found or has no content.")
        
        # Handle content-based request
        elif request.content:
            content = request.content
            if not content.strip():
                raise HTTPException(status_code=400, detail="Content cannot be empty.")
        
        else:
            raise HTTPException(status_code=400, detail="Either document_id or content must be provided.")
        
        prompt_tpl = PROMPT_REGISTRY["qa_pair_generator"]
        app_logger.log_debug(f"Using prompt template: {prompt_tpl.name}")
        
        # Prepare content with context if available
        full_content = content[:3000]
        if request.context:
            full_content = f"Context: {request.context}\n\nContent: {full_content}"
        
        app_logger.log_debug(f"Full content for Q&A generation: {full_content}")
        prompt = prompt_tpl.render(content=full_content, num_pairs=request.num_pairs)
        app_logger.log_debug(f"Rendered prompt: {prompt[:500]}...")
        
        async with GenerativeResponder() as responder:
            raw = await responder.generate_text(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
        
        cleaned_raw = extract_json_from_codeblock(raw)
        app_logger.log_debug(f"Raw LLM response: {raw}")
        app_logger.log_debug(f"Cleaned JSON: {cleaned_raw}")
        
        try:
            parsed_json = json.loads(cleaned_raw)
            app_logger.log_debug(f"Parsed JSON type: {type(parsed_json)}, content: {parsed_json}")
            
            # Handle both array format and object format
            if isinstance(parsed_json, list):
                qa_list = [QAPair(**item) for item in parsed_json]
            elif isinstance(parsed_json, dict) and "qa_pairs" in parsed_json:
                qa_list = [QAPair(**item) for item in parsed_json["qa_pairs"]]
            else:
                app_logger.log_error(f"Unexpected JSON structure: {parsed_json}")
                raise ValueError(f"Expected array or object with 'qa_pairs' key, got: {type(parsed_json)}")
                
        except json.JSONDecodeError as e:
            app_logger.log_error(f"JSON decode error: {e}")
            app_logger.log_error(f"Raw response that failed to parse: {cleaned_raw}")
            raise HTTPException(status_code=502, detail=f"Invalid JSON from LLM: {str(e)}")
        except Exception as e:
            app_logger.log_error(f"Failed to parse Q&A pairs: {e}")
            app_logger.log_error(f"Parsed JSON: {parsed_json if 'parsed_json' in locals() else 'Not parsed'}")
            raise HTTPException(status_code=502, detail=f"Failed to process QA request: {str(e)}")
        
        return QAResponse(
            document_id=document_id,
            content_preview=content[:200] + "..." if len(content) > 200 else content if content else None,
            qa_pairs=qa_list
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"Error in QA endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process QA request: {str(e)}")