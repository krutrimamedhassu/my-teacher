from fastapi import APIRouter, HTTPException, Body, Query, Path, Request
from fastapi.responses import JSONResponse
from typing import Optional, List, Any
from app.conversations.conversation_handler import ConversationManager
import os
import json
from datetime import datetime, UTC
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
    app_logger.log_info(f"[ConversationsAPI] Starting create_conversation_with_id - conversation_id: {conversation_id}, user_id: {user_id}, username: {username}, title: {title}")
    try:
        conv = ConversationManager.create_conversation_with_id(
            conversation_id=conversation_id,
            user_id=user_id,
            username=username,
            title=title
        )
        app_logger.log_info(f"[ConversationsAPI] Successfully created conversation with ID: {conv['conversation_id']}")
        return {"conversation_id": conv["conversation_id"], "conversation": conv}
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in create_conversation_with_id: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", summary="Create a new conversation")
def create_conversation(user_id: Optional[str] = Body(None), username: Optional[str] = Body(None), title: Optional[str] = Body(None)):
    app_logger.log_info(f"[ConversationsAPI] Starting create_conversation - user_id: {user_id}, username: {username}, title: {title}")
    try:
        conv = ConversationManager.create_conversation(user_id=user_id, username=username, title=title)
        app_logger.log_info(f"[ConversationsAPI] Successfully created conversation with ID: {conv['conversation_id']}")
        return conv
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in create_conversation: {str(e)}")
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
    app_logger.log_info(f"[ConversationsAPI] Starting add_message - conversation_id: {conversation_id}, sender_id: {sender_id}, role: {role}")
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
        app_logger.log_info(f"[ConversationsAPI] Successfully added message to conversation {conversation_id}")
        return msg
    except FileNotFoundError as e:
        app_logger.log_error(f"[ConversationsAPI] Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in add_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}", summary="Get a conversation by ID")
def get_conversation(conversation_id: str):
    app_logger.log_info(f"[ConversationsAPI] Starting get_conversation - conversation_id: {conversation_id}")
    try:
        conversation = ConversationManager.get_conversation(conversation_id)
        app_logger.log_info(f"[ConversationsAPI] Successfully retrieved conversation {conversation_id}")
        return conversation
    except FileNotFoundError as e:
        app_logger.log_error(f"[ConversationsAPI] Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in get_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", summary="List all conversations for a user")
def list_conversations_for_user(user_id: str):
    app_logger.log_info(f"[ConversationsAPI] Starting list_conversations_for_user - user_id: {user_id}")
    try:
        conversations = ConversationManager.list_conversations_for_user(user_id)
        app_logger.log_info(f"[ConversationsAPI] Successfully retrieved {len(conversations)} conversations for user {user_id}")
        return conversations
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in list_conversations_for_user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anonymous", summary="List all anonymous conversations")
def list_conversations_anonymous():
    app_logger.log_info("[ConversationsAPI] Starting list_conversations_anonymous")
    try:
        conversations = ConversationManager.list_conversations_anonymous()
        app_logger.log_info(f"[ConversationsAPI] Successfully retrieved {len(conversations)} anonymous conversations")
        return conversations
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in list_conversations_anonymous: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{conversation_id}", summary="Edit a conversation (title, is_active)")
def edit_conversation(
    conversation_id: str = Path(..., description="Conversation ID to edit"),
    title: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None)
):
    app_logger.log_info(f"[ConversationsAPI] Starting edit_conversation - conversation_id: {conversation_id}, title: {title}, is_active: {is_active}")
    try:
        from app.conversations.conversation_handler import _conv_path
        path = _conv_path(conversation_id)
        if not os.path.exists(path):
            app_logger.log_error(f"[ConversationsAPI] Conversation not found: {conversation_id}")
            raise HTTPException(status_code=404, detail="Conversation not found")
        with open(path, 'r') as f:
            conversation = json.load(f)
        updated = False
        if title is not None:
            conversation['title'] = title
            updated = True
        if is_active is not None:
            conversation['is_active'] = is_active
            updated = True
        if updated:
            conversation['updated_at'] = datetime.now(UTC).isoformat()
            with open(path, 'w') as f:
                json.dump(conversation, f, indent=2)
            app_logger.log_info(f"[ConversationsAPI] Successfully updated conversation {conversation_id}")
        else:
            app_logger.log_info(f"[ConversationsAPI] No changes made to conversation {conversation_id}")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in edit_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/empty", summary="Delete all empty conversations for the authenticated user (hard delete)")
async def delete_empty_conversations(http_request: Request) -> JSONResponse:
    """
    Hard-delete (remove JSON files) for all conversations that have zero messages for the current authenticated user.
    Authentication is required (JWT or API key).
    """
    app_logger.log_info("[ConversationsAPI] Starting delete_empty_conversations")
    try:
        from app.core.auth.optional_auth import require_auth_with_usage_tracking
        from app.conversations.conversation_handler import _conv_path

        # Authenticate user (required)
        user_id, identifier, usage_info, response_headers = await require_auth_with_usage_tracking(
            http_request, "conversations_delete_empty"
        )
        app_logger.log_info(f"[ConversationsAPI] Authenticated user for delete_empty_conversations: {user_id}")

        # Get user's conversations (summary) and then inspect each full record
        user_conversations = ConversationManager.list_conversations_for_user(user_id)

        deleted_ids = []
        skipped_ids = []

        for conv_summary in user_conversations:
            conv_id = conv_summary.get("conversation_id")
            if not conv_id:
                continue

            path = _conv_path(conv_id)
            if not os.path.exists(path):
                continue

            try:
                with open(path, 'r') as f:
                    conversation = json.load(f)
            except Exception:
                skipped_ids.append(conv_id)
                continue

            # Only hard delete if has zero messages
            messages = conversation.get('messages', [])
            if len(messages) == 0:
                try:
                    os.remove(path)
                    deleted_ids.append(conv_id)
                except Exception:
                    skipped_ids.append(conv_id)
            else:
                skipped_ids.append(conv_id)

        result = {
            "deleted_count": len(deleted_ids),
            "deleted_ids": deleted_ids,
            "skipped_count": len(skipped_ids)
        }
        app_logger.log_info(f"[ConversationsAPI] Successfully deleted {len(deleted_ids)} empty conversations for user {user_id}")
        return JSONResponse(status_code=200, content=result, headers=response_headers)
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in delete_empty_conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{conversation_id}", summary="Delete a conversation (soft delete)")
def delete_conversation(
    conversation_id: str = Path(..., description="Conversation ID to delete")
):
    app_logger.log_info(f"[ConversationsAPI] Starting delete_conversation - conversation_id: {conversation_id}")
    try:
        from app.conversations.conversation_handler import _conv_path
        path = _conv_path(conversation_id)
        if not os.path.exists(path):
            app_logger.log_error(f"[ConversationsAPI] Conversation not found: {conversation_id}")
            raise HTTPException(status_code=404, detail="Conversation not found")
        with open(path, 'r') as f:
            conversation = json.load(f)
        conversation['deleted'] = True
        conversation['is_active'] = False
        conversation['updated_at'] = datetime.now(UTC).isoformat()
        with open(path, 'w') as f:
            json.dump(conversation, f, indent=2)
        app_logger.log_info(f"[ConversationsAPI] Successfully soft-deleted conversation {conversation_id}")
        return {"detail": "Conversation deleted", "conversation": conversation}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in delete_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/sidebar_info", summary="Get all sidebar_info entries from a conversation")
def get_conversation_sidebar_info(conversation_id: str):
    app_logger.log_info(f"[ConversationsAPI] Starting get_conversation_sidebar_info - conversation_id: {conversation_id}")
    try:
        conversation = ConversationManager.get_conversation(conversation_id)
        sidebar_info_list = []
        
        for message in conversation.get('messages', []):
            if 'sidebar_info' in message and message['sidebar_info'] is not None:
                sidebar_info_list.append({
                    'message_id': message.get('message_id'),
                    'timestamp': message.get('timestamp'),
                    'role': message.get('role'),
                    'sidebar_info': message['sidebar_info']
                })
        
        result = {
            "conversation_id": conversation_id,
            "sidebar_info_count": len(sidebar_info_list),
            "sidebar_info_list": sidebar_info_list
        }
        app_logger.log_info(f"[ConversationsAPI] Successfully retrieved {len(sidebar_info_list)} sidebar_info entries for conversation {conversation_id}")
        return result
    except FileNotFoundError as e:
        app_logger.log_error(f"[ConversationsAPI] Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in get_conversation_sidebar_info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/documents", summary="Add document to conversation")
async def add_document_to_conversation(
    conversation_id: str,
    document_id: str = Body(...),
    request: Request = None
):
    """Add a document to a specific conversation"""
    app_logger.log_info(f"[ConversationsAPI] Starting add_document_to_conversation - conversation_id: {conversation_id}, document_id: {document_id}")
    try:
        from app.core.auth.optional_auth import require_auth_with_usage_tracking
        from app.core.data.document_store import document_store
        # Authenticate user
        user_id, identifier, usage_info, response_headers = await require_auth_with_usage_tracking(
            request, "conversation_add_document"
        )
        
        # Verify conversation exists and user has access
        conversation = ConversationManager.get_conversation(conversation_id)
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Verify document exists
        document = await document_store.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Add document to conversation
        if 'documents' not in conversation:
            conversation['documents'] = []
            
        # Check if document already exists in conversation
        if any(doc['document_id'] == document_id for doc in conversation['documents']):
            raise HTTPException(status_code=409, detail="Document already in conversation")
            
        doc_entry = {
            'document_id': document_id,
            'filename': document['filename'],
            'file_type': document['file_type'],
            'added_at': datetime.now(UTC).isoformat(),
            'added_by': user_id
        }
        
        conversation['documents'].append(doc_entry)
        conversation['updated_at'] = datetime.now(UTC).isoformat()

        # Save conversation
        from app.conversations.conversation_handler import _conv_path
        path = _conv_path(conversation_id)
        with open(path, 'w') as f:
            json.dump(conversation, f, indent=2)
        
        app_logger.log_info(f"[ConversationsAPI] Successfully added document {document_id} to conversation {conversation_id}")
        return JSONResponse(
            status_code=200,
            content={
                "message": "Document added to conversation",
                "document": doc_entry
            },
            headers=response_headers
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in add_document_to_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/documents", summary="Get all documents in conversation")
async def get_conversation_documents(
    conversation_id: str,
    request: Request = None
):
    """Get all documents associated with a conversation"""
    app_logger.log_info(f"[ConversationsAPI] Starting get_conversation_documents - conversation_id: {conversation_id}")
    try:
        from app.core.auth.optional_auth import require_auth_with_usage_tracking
        from app.core.data.document_store import document_store
        # Authenticate user
        user_id, identifier, usage_info, response_headers = await require_auth_with_usage_tracking(
            request, "conversation_get_documents"
        )
        
        # Verify conversation exists and user has access
        conversation = ConversationManager.get_conversation(conversation_id)
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        documents = conversation.get('documents', [])
        
        # Enrich with document metadata
        enriched_docs = []
        for doc_entry in documents:
            document = await document_store.get_document(doc_entry['document_id'])
            if document:
                enriched_doc = {**doc_entry}
                enriched_doc['file_size'] = document.get('file_size')
                enriched_doc['upload_date'] = document.get('upload_date')
                enriched_doc['metadata'] = document.get('metadata', {})
                enriched_docs.append(enriched_doc)
        
        app_logger.log_info(f"[ConversationsAPI] Successfully retrieved {len(enriched_docs)} documents for conversation {conversation_id}")
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({
                "conversation_id": conversation_id,
                "documents": enriched_docs,
                "total_count": len(enriched_docs)
            }),
            headers=response_headers
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in get_conversation_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{conversation_id}/documents/{document_id}", summary="Remove document from conversation")
async def remove_document_from_conversation(
    conversation_id: str,
    document_id: str,
    delete_references: bool = Query(True, description="Also remove document references from messages"),
    request: Request = None
):
    """Remove a document from conversation and optionally clean up references"""
    app_logger.log_info(f"[ConversationsAPI] Starting remove_document_from_conversation - conversation_id: {conversation_id}, document_id: {document_id}, delete_references: {delete_references}")
    try:
        from app.core.auth.optional_auth import require_auth_with_usage_tracking
        # Authenticate user
        user_id, identifier, usage_info, response_headers = await require_auth_with_usage_tracking(
            request, "conversation_remove_document"
        )
        
        # Verify conversation exists and user has access
        conversation = ConversationManager.get_conversation(conversation_id)
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Remove document from documents list
        documents = conversation.get('documents', [])
        original_count = len(documents)
        conversation['documents'] = [doc for doc in documents if doc['document_id'] != document_id]
        
        if len(conversation['documents']) == original_count:
            raise HTTPException(status_code=404, detail="Document not found in conversation")
        
        # Clean up references from messages if requested
        references_cleaned = 0
        if delete_references:
            for message in conversation.get('messages', []):
                # Clean attachments that reference this document
                if 'attachments' in message and message['attachments']:
                    original_attachments = len(message['attachments'])
                    message['attachments'] = [
                        att for att in message['attachments'] 
                        if att.get('document_id') != document_id
                    ]
                    if len(message['attachments']) < original_attachments:
                        references_cleaned += 1
                
                # Clean sidebar_info that might reference this document
                if 'sidebar_info' in message and message['sidebar_info']:
                    sidebar_info = message['sidebar_info']
                    if isinstance(sidebar_info, dict) and sidebar_info.get('document_id') == document_id:
                        message['sidebar_info'] = None
                        references_cleaned += 1
        
        conversation['updated_at'] = datetime.now(UTC).isoformat()

        # Save conversation
        from app.conversations.conversation_handler import _conv_path
        path = _conv_path(conversation_id)
        with open(path, 'w') as f:
            json.dump(conversation, f, indent=2)
        
        app_logger.log_info(f"[ConversationsAPI] Successfully removed document {document_id} from conversation {conversation_id}, cleaned {references_cleaned} references")
        return JSONResponse(
            status_code=200,
            content={
                "message": "Document removed from conversation",
                "references_cleaned": references_cleaned,
                "remaining_documents": len(conversation['documents'])
            },
            headers=response_headers
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[ConversationsAPI] Error in remove_document_from_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
