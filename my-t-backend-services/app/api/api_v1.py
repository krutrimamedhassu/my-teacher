from fastapi import APIRouter

from app.api.endpoints import (
    health,
    docs,
    scraper,
    responder,
    upload,
    document_qa,
    auth,
    conversations,
    streaming,
    websocket,
    ai_keys,
    flashcards,
    breakdowns,
    explanations,
    key_concepts,
    multiple_choice_questions,
    question_paper,
    study_plan,
    visuals,
    speech,
    contact
)

from app.logger.app_logger import app_logger

# Create the main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(docs.router, prefix="/docs", tags=["docs"])
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])
api_router.include_router(responder.router, prefix="/responder", tags=["responder"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(document_qa.router, prefix="/document-qa", tags=["document-qa"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(streaming.router, prefix="/streaming", tags=["streaming"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(ai_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["flashcards"])
api_router.include_router(breakdowns.router, prefix="/breakdowns", tags=["breakdowns"])
api_router.include_router(explanations.router, prefix="/explanations", tags=["explanations"])
api_router.include_router(key_concepts.router, prefix="/key-concepts", tags=["key-concepts"])
api_router.include_router(multiple_choice_questions.router, prefix="/multiple-choice-questions", tags=["multiple-choice-questions"])
api_router.include_router(question_paper.router, prefix="/qa", tags=["question-answer"])
api_router.include_router(study_plan.router, prefix="/study-plan", tags=["study-plan"])
api_router.include_router(visuals.router, prefix="/visuals", tags=["visuals"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])

app_logger.log_info("API router configured with all endpoints")