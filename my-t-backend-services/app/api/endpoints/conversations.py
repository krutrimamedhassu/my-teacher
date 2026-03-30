from fastapi import APIRouter, HTTPException, Body, Query, Path, Request
from fastapi.responses import JSONResponse
from typing import Optional, List, Any
from app.context_store.conversation_store import ConversationManager
from fastapi.encoders import jsonable_encoder
from app.logger.app_logger import app_logger

router = APIRouter(tags=["conversations"])


@router.post("/create_id", summary="Create a conversation with a specific or generated conversation_id")
def create_conversation_with_id(
    conversation_id: Optional[str] = Body(None),
    user_id: Optional[str] = Body(None),
    username: Optional[str] = Body(None),
    title: Optional[str] = Body(None)
):
    app_logger.log_info(f"[ConversationsAPI] create_conversation_with_id conversation_id={conversation_id}")
    try:
        conv = ConversationManager.create_conversation_with_id(
            conversation_id=conversation_id, user_id=user_id, username=username, title=title
        )
        return {"conversation_id": conv["conversation_id"], "conversation": conv}
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in create_conversation_with_id: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="Create a new conversation")
def create_conversation(
    user_id: Optional[str] = Body(None),
    username: Optional[str] = Body(None),
    title: Optional[str] = Body(None)
):
    app_logger.log_info(f"[ConversationsAPI] create_conversation user_id={user_id}")
    try:
        conv = ConversationManager.create_conversation(user_id=user_id, username=username, title=title)
        return conv
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in create_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", summary="Add a message to a conversation")
def add_message(
    conversation_id: str,
    sender_id: Optional[str] = Body(None),
    sender_username: Optional[str] = Body(None),
    role: str = Body(...),
    text: str = Body(...),
    attachments: Optional[List[Any]] = Body(None),
    sidebar_info: Optional[dict] = Body(None)
):
    app_logger.log_info(f"[ConversationsAPI] add_message conversation_id={conversation_id} role={role}")
    try:
        msg = ConversationManager.append_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_username=sender_username,
            role=role,
            text=text,
            attachments=attachments,
            sidebar_info=sidebar_info
        )
        return msg
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in add_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", summary="List all conversations for a user")
def list_conversations_for_user(user_id: str):
    app_logger.log_info(f"[ConversationsAPI] list_conversations_for_user user_id={user_id}")
    try:
        return ConversationManager.list_conversations_for_user(user_id)
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in list_conversations_for_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anonymous", summary="List all anonymous conversations")
def list_conversations_anonymous():
    app_logger.log_info("[ConversationsAPI] list_conversations_anonymous")
    try:
        return ConversationManager.list_conversations_anonymous()
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in list_conversations_anonymous: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/empty", summary="Delete all empty conversations for the authenticated user")
async def delete_empty_conversations(http_request: Request) -> JSONResponse:
    app_logger.log_info("[ConversationsAPI] delete_empty_conversations")
    try:
        from app.core.auth.optional_auth import require_auth_with_usage_tracking
        user_id, identifier, usage_info, response_headers = await require_auth_with_usage_tracking(
            http_request, "conversations_delete_empty"
        )
        result = ConversationManager.delete_empty_conversations_for_user(user_id)
        return JSONResponse(status_code=200, content=result, headers=response_headers)
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in delete_empty_conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cleanup", summary="Delete expired conversations (cron job)")
def cleanup_conversations():
    app_logger.log_info("[ConversationsAPI] cleanup_conversations")
    try:
        result = ConversationManager.cleanup_expired_conversations()
        return result
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in cleanup_conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples", summary="List all example/demo conversations")
def list_example_conversations():
    app_logger.log_info("[ConversationsAPI] list_example_conversations")
    try:
        return ConversationManager.list_example_conversations()
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in list_example_conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", summary="Get a conversation by ID")
def get_conversation(conversation_id: str):
    app_logger.log_info(f"[ConversationsAPI] get_conversation {conversation_id}")
    try:
        return ConversationManager.get_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in get_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{conversation_id}", summary="Edit a conversation (title, is_active)")
def edit_conversation(
    conversation_id: str = Path(...),
    title: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None)
):
    app_logger.log_info(f"[ConversationsAPI] edit_conversation {conversation_id}")
    try:
        return ConversationManager.edit_conversation(conversation_id, title=title, is_active=is_active)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in edit_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}", summary="Delete a conversation (soft delete)")
def delete_conversation(conversation_id: str = Path(...)):
    app_logger.log_info(f"[ConversationsAPI] delete_conversation {conversation_id}")
    try:
        conv = ConversationManager.delete_conversation(conversation_id)
        return {"detail": "Conversation deleted", "conversation": conv}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in delete_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/sidebar_info", summary="Get all sidebar_info entries from a conversation")
def get_conversation_sidebar_info(conversation_id: str):
    app_logger.log_info(f"[ConversationsAPI] get_conversation_sidebar_info {conversation_id}")
    try:
        conversation = ConversationManager.get_conversation(conversation_id)
        sidebar_info_list = [
            {
                'message_id': msg.get('message_id'),
                'timestamp': msg.get('timestamp'),
                'role': msg.get('role'),
                'sidebar_info': msg['sidebar_info']
            }
            for msg in conversation.get('messages', [])
            if msg.get('sidebar_info') is not None
        ]
        return {
            "conversation_id": conversation_id,
            "sidebar_info_count": len(sidebar_info_list),
            "sidebar_info_list": sidebar_info_list
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in get_conversation_sidebar_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/documents", summary="Add document to conversation")
async def add_document_to_conversation(
    conversation_id: str,
    document_id: str = Body(...),
    request: Request = None
):
    app_logger.log_info(f"[ConversationsAPI] add_document_to_conversation {conversation_id} doc={document_id}")
    try:
        from app.core.auth.optional_auth import require_auth_with_usage_tracking
        from app.core.data.document_store import document_store
        user_id, identifier, usage_info, response_headers = await require_auth_with_usage_tracking(
            request, "conversation_add_document"
        )
        conversation = ConversationManager.get_conversation(conversation_id)
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        document = await document_store.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        doc_metadata = {'filename': document['filename'], 'file_type': document['file_type']}
        added = ConversationManager.add_document_to_conversation(conversation_id, document_id, doc_metadata, user_id)
        if not added:
            raise HTTPException(status_code=409, detail="Document already in conversation")
        doc_entry = {
            'document_id': document_id,
            'filename': document['filename'],
            'file_type': document['file_type'],
        }
        return JSONResponse(
            status_code=200,
            content={"message": "Document added to conversation", "document": doc_entry},
            headers=response_headers
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in add_document_to_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/documents", summary="Get all documents in conversation")
async def get_conversation_documents(conversation_id: str, request: Request = None):
    app_logger.log_info(f"[ConversationsAPI] get_conversation_documents {conversation_id}")
    try:
        from app.core.auth.auth_dependency import get_current_user
        from app.core.data.document_store import document_store
        user = await get_current_user(request)
        user_id = str(user.get('_id') or user.get('user_id') or user.get('id'))
        conversation = ConversationManager.get_conversation(conversation_id)
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        documents = conversation.get('documents', [])
        enriched_docs = []
        for doc_entry in documents:
            document = await document_store.get_document(doc_entry['document_id'])
            if document:
                enriched_docs.append({
                    **doc_entry,
                    'file_size': document.get('file_size'),
                    'upload_date': document.get('upload_date'),
                    'metadata': document.get('metadata', {})
                })
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({"conversation_id": conversation_id, "documents": enriched_docs, "total_count": len(enriched_docs)}),
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in get_conversation_documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}/documents/{document_id}", summary="Remove document from conversation")
async def remove_document_from_conversation(
    conversation_id: str,
    document_id: str,
    delete_references: bool = Query(True),
    request: Request = None
):
    app_logger.log_info(f"[ConversationsAPI] remove_document_from_conversation {conversation_id} doc={document_id}")
    try:
        from app.core.auth.optional_auth import require_auth_with_usage_tracking
        user_id, identifier, usage_info, response_headers = await require_auth_with_usage_tracking(
            request, "conversation_remove_document"
        )
        conversation = ConversationManager.get_conversation(conversation_id)
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if not any(d['document_id'] == document_id for d in conversation.get('documents', [])):
            raise HTTPException(status_code=404, detail="Document not found in conversation")
        references_cleaned = ConversationManager.remove_document_from_conversation(
            conversation_id, document_id, cleanup_references=delete_references
        )
        remaining = len([d for d in conversation.get('documents', []) if d['document_id'] != document_id])
        return JSONResponse(
            status_code=200,
            content={"message": "Document removed from conversation", "references_cleaned": references_cleaned, "remaining_documents": remaining},
            headers=response_headers
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in remove_document_from_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
