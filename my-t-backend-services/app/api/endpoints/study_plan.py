import json
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.logger.app_logger import app_logger
from app.core.prompts import STUDY_PLAN_PROMPT
from app.core.response.generative_responder import GenerativeResponder
from app.core.utils.endpoint_utils import extract_json_from_codeblock

router = APIRouter()


class KnowledgeLevel(str, Enum):
    """Enum for student knowledge levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StudyPlanRequest(BaseModel):
    """Request model for generating a personalized study plan."""
    content: str = Field(..., description="Content to study")
    subject_area: str = Field(..., description="Subject area of the content")
    knowledge_level: KnowledgeLevel = Field(KnowledgeLevel.INTERMEDIATE, description="Student's current knowledge level")
    hours_per_day: float = Field(2.0, description="Available study time per day in hours", gt=0, le=24)
    deadline: Optional[str] = Field(None, description="Deadline for studying (YYYY-MM-DD format)")
    learning_goals: List[str] = Field(..., description="Learning goals for the study plan")
    days_until_deadline: Optional[int] = Field(None, description="Number of days for the study plan (overrides deadline if provided)")


class StudySession(BaseModel):
    """Model for a study session."""
    day: int
    date: Optional[str] = None
    duration_hours: float
    topics: List[str]
    activities: List[str]
    resources: List[str]
    priority: str  # "high", "medium", "low"
    estimated_difficulty: str  # "easy", "moderate", "challenging"
    learning_objectives: List[str]


class StudyPlanResponse(BaseModel):
    """Response model for study plan generation."""
    study_sessions: List[StudySession]
    subject_area: str
    knowledge_level: KnowledgeLevel
    total_days: int
    total_hours: float
    learning_goals: List[str]
    deadline: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the study plan")


@router.post(
    "",
    response_model=StudyPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Personalized Study Plan",
    description="Generate a personalized study plan based on content, knowledge level, and deadline using AI analysis."
)
async def generate_study_plan(request: StudyPlanRequest) -> StudyPlanResponse:
    """
    Generate a personalized study plan using AI analysis of the content.
    
    Args:
        request: Request containing content and study plan parameters
        
    Returns:
        StudyPlanResponse: AI-generated personalized study plan
    """
    app_logger.log_info(f"[StudyPlan] Generating plan for subject: {request.subject_area}, level: {request.knowledge_level}")
    
    try:
        # Use days_until_deadline from request if provided, else calculate from deadline
        days_until_deadline = request.days_until_deadline
        if days_until_deadline is None and request.deadline:
            try:
                deadline_date = datetime.strptime(request.deadline, "%Y-%m-%d")
                today = datetime.now()
                days_until_deadline = (deadline_date - today).days
                if days_until_deadline < 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Deadline must be in the future"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid deadline format. Use YYYY-MM-DD"
                )
        
        # Render the prompt with all parameters
        prompt = STUDY_PLAN_PROMPT.render(
            content=request.content,
            subject_area=request.subject_area,
            knowledge_level=request.knowledge_level,
            hours_per_day=request.hours_per_day,
            deadline=request.deadline or "flexible",
            days_until_deadline=days_until_deadline if days_until_deadline is not None else "not specified",
            learning_goals=", ".join(request.learning_goals)
        )
        app_logger.log_debug(f"[StudyPlan] Prompt (truncated): {prompt[:200]}...")
        
        # Call the LLM with proper cleanup
        try:
            async with GenerativeResponder() as responder:
                raw_text = await responder.generate_text(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                app_logger.log_debug(f"[StudyPlan] Raw LLM response: {raw_text[:500]}...")
        except Exception as e:
            app_logger.log_error(f"[StudyPlan] LLM call failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM service error when generating study plan."
            )
        
        # Parse JSON response - handle markdown code blocks
        try:
            cleaned_raw = extract_json_from_codeblock(raw_text)
            app_logger.log_debug(f"[StudyPlan] Extracted JSON: {cleaned_raw[:200]}...")
            payload: Dict[str, Any] = json.loads(cleaned_raw)
        except json.JSONDecodeError as e:
            app_logger.log_error(f"[StudyPlan] JSON parse error: {e}")
            app_logger.log_debug(f"[StudyPlan] Raw LLM response: {raw_text[:500]}...")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Received malformed JSON from LLM."
            )
        
        # Validate and extract study sessions
        study_sessions_raw = payload.get("study_sessions")
        if not isinstance(study_sessions_raw, list) or not study_sessions_raw:
            app_logger.log_error(f"[StudyPlan] LLM returned invalid study_sessions: {study_sessions_raw}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM did not return a valid study_sessions list."
            )
        
        # Convert raw sessions to StudySession models
        study_sessions: List[StudySession] = []
        for idx, session_raw in enumerate(study_sessions_raw):
            try:
                # Ensure required fields are present
                if not all(k in session_raw for k in ["day", "topics", "activities", "resources", "priority"]):
                    raise ValueError(f"Missing required fields in session {idx}")
                
                # Set default values for optional fields
                session_data = {
                    "day": session_raw["day"],
                    "duration_hours": session_raw.get("duration_hours", request.hours_per_day),
                    "topics": session_raw["topics"],
                    "activities": session_raw["activities"],
                    "resources": session_raw["resources"],
                    "priority": session_raw["priority"],
                    "estimated_difficulty": session_raw.get("estimated_difficulty", "moderate"),
                    "learning_objectives": session_raw.get("learning_objectives", [])
                }
                
                # Calculate date if not provided
                if "date" not in session_raw:
                    today = datetime.now()
                    session_date = (today + timedelta(days=session_raw["day"]-1)).strftime("%Y-%m-%d")
                    session_data["date"] = session_date
                else:
                    session_data["date"] = session_raw["date"]
                
                study_sessions.append(StudySession(**session_data))
                
            except Exception as e:
                app_logger.log_error(f"[StudyPlan] Invalid session schema at index {idx}: {session_raw} — {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Malformed study session structure returned by LLM."
                )
        
        # Calculate metadata
        total_days = len(study_sessions)
        total_hours = sum(session.duration_hours for session in study_sessions)
        
        # Extract additional metadata from LLM response
        metadata = {
            "content_analysis": payload.get("content_analysis", {}),
            "learning_strategy": payload.get("learning_strategy", "adaptive"),
            "estimated_completion_time": f"{total_hours:.1f} hours",
            "difficulty_distribution": payload.get("difficulty_distribution", {}),
            "recommended_pace": payload.get("recommended_pace", "moderate"),
            "success_metrics": payload.get("success_metrics", []),
            "adaptation_notes": payload.get("adaptation_notes", [])
        }
        
        app_logger.log_info(f"[StudyPlan] Successfully generated {total_days} study sessions ({total_hours:.1f} hours)")
        
        return StudyPlanResponse(
            study_sessions=study_sessions,
            subject_area=request.subject_area,
            knowledge_level=request.knowledge_level,
            total_days=total_days,
            total_hours=total_hours,
            learning_goals=request.learning_goals,
            deadline=request.deadline,
            metadata=metadata
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        app_logger.log_error(f"[StudyPlan] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study plan: {str(e)}"
        )