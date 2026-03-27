import os
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio
from app.core.response.generative_responder import GenerativeResponder
from app.logger.app_logger import app_logger

_default_conv_dir = os.path.join(os.path.dirname(__file__), 'data')
CONV_DATA_DIR = _default_conv_dir if os.access(os.path.dirname(__file__), os.W_OK) else '/tmp/conversations/data'
os.makedirs(CONV_DATA_DIR, exist_ok=True)

def _now():
    app_logger.log_debug("[ConversationManager] Getting current UTC timestamp")
    result = datetime.utcnow().isoformat()
    app_logger.log_debug(f"[ConversationManager] Generated timestamp: {result}")
    return result

def _conv_path(conversation_id: str) -> str:
    app_logger.log_debug(f"[ConversationManager] Generating path for conversation_id: {conversation_id}")
    path = os.path.join(CONV_DATA_DIR, f'{conversation_id}.json')
    app_logger.log_debug(f"[ConversationManager] Generated path: {path}")
    return path

class ConversationManager:
    @staticmethod
    def create_conversation(user_id: Optional[str] = None, username: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] Starting create_conversation for user_id: {user_id}, username: {username}, title: {title}")
        try:
            conversation_id = str(uuid.uuid4())
            app_logger.log_debug(f"[ConversationManager] Generated conversation_id: {conversation_id}")
            now = _now()
            conversation = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'username': username or 'Anonymous',
                'title': title or 'Untitled Conversation',
                'created_at': now,
                'updated_at': now,
                'is_active': True,
                'deleted': False,
                'last_message_preview': '',
                'messages': []
            }
            with open(_conv_path(conversation_id), 'w') as f:
                json.dump(conversation, f, indent=2)
            app_logger.log_info(f"[ConversationManager] Successfully created conversation with ID: {conversation_id}")
            return conversation
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in create_conversation: {str(e)}")
            raise

    @staticmethod
    def create_conversation_with_id(conversation_id: Optional[str] = None, user_id: Optional[str] = None, username: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] Starting create_conversation_with_id for conversation_id: {conversation_id}, user_id: {user_id}, username: {username}, title: {title}")
        try:
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
                app_logger.log_debug(f"[ConversationManager] Generated new conversation_id: {conversation_id}")
            now = _now()
            conversation = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'username': username or 'Anonymous',
                'title': title or 'Untitled Conversation',
                'created_at': now,
                'updated_at': now,
                'is_active': True,
                'deleted': False,
                'last_message_preview': '',
                'messages': []
            }
            with open(_conv_path(conversation_id), 'w') as f:
                json.dump(conversation, f, indent=2)
            app_logger.log_info(f"[ConversationManager] Successfully created conversation with specific ID: {conversation_id}")
            return conversation
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in create_conversation_with_id: {str(e)}")
            raise

    @staticmethod
    def append_message(conversation_id: str, sender_id: Optional[str], sender_username: Optional[str], role: str, text: str, attachments: Optional[List[Any]] = None, sidebar_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] Starting append_message for conversation_id: {conversation_id}, sender_id: {sender_id}, role: {role}")
        try:
            path = _conv_path(conversation_id)
            if not os.path.exists(path):
                app_logger.log_error(f"[ConversationManager] Conversation not found at path: {path}")
                raise FileNotFoundError('Conversation not found')
            with open(path, 'r') as f:
                conversation = json.load(f)
            message = {
                'message_id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'sender_id': sender_id,
                'sender_username': sender_username or 'Anonymous',
                'role': role,
                'text': text,
                'attachments': attachments or [],
                'timestamp': _now()
            }
            # Store sidebar_info as a nested field if provided
            if sidebar_info:
                message['sidebar_info'] = sidebar_info
            conversation['messages'].append(message)
            conversation['updated_at'] = message['timestamp']
            conversation['last_message_preview'] = text[:100]
            # Auto-name the conversation on the first message using AI
            if len(conversation['messages']) == 1:
                try:
                    loop = None
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        pass
                    if loop and loop.is_running():
                        # If already in an event loop (unlikely in sync context), create a new task
                        async def generate_title_async():
                            async with GenerativeResponder() as responder:
                                return await responder.generate_title(text)
                        title = loop.run_until_complete(generate_title_async())
                    else:
                        async def generate_title_async():
                            async with GenerativeResponder() as responder:
                                return await responder.generate_title(text)
                        title = asyncio.run(generate_title_async())
                    conversation['title'] = title
                except Exception:
                    # Fallback: Use first 4 words or up to 30 chars
                    words = text.strip().split()
                    title = ' '.join(words[:4])
                    if len(title) > 30:
                        title = title[:27] + '...'
                    conversation['title'] = title
                    app_logger.log_info(f"[ConversationManager] Auto-generated conversation title: {title}")
            with open(path, 'w') as f:
                json.dump(conversation, f, indent=2)
            app_logger.log_info(f"[ConversationManager] Successfully appended message to conversation {conversation_id}")
            return message
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in append_message: {str(e)}")
            raise

    @staticmethod
    def get_conversation(conversation_id: str) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] Starting get_conversation for conversation_id: {conversation_id}")
        try:
            path = _conv_path(conversation_id)
            if not os.path.exists(path):
                app_logger.log_error(f"[ConversationManager] Conversation not found at path: {path}")
                raise FileNotFoundError('Conversation not found')
            with open(path, 'r') as f:
                conversation = json.load(f)
            app_logger.log_info(f"[ConversationManager] Successfully retrieved conversation {conversation_id}")
            return conversation
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in get_conversation: {str(e)}")
            raise

    @staticmethod
    def list_conversations_for_user(user_id: str) -> List[Dict[str, Any]]:
        app_logger.log_info(f"[ConversationManager] Starting list_conversations_for_user for user_id: {user_id}")
        try:
            conversations = []
            for fname in os.listdir(CONV_DATA_DIR):
                if fname.endswith('.json'):
                    with open(os.path.join(CONV_DATA_DIR, fname), 'r') as f:
                        conv = json.load(f)
                        if conv.get('user_id') == user_id and not conv.get('deleted', False):
                            conversations.append({
                                'conversation_id': conv['conversation_id'],
                                'title': conv.get('title', ''),
                                'created_at': conv['created_at'],
                                'updated_at': conv['updated_at'],
                                'last_message_preview': conv.get('last_message_preview', ''),
                                'is_active': conv.get('is_active', True)
                            })
            result = sorted(conversations, key=lambda x: x['updated_at'], reverse=True)
            app_logger.log_info(f"[ConversationManager] Successfully retrieved {len(result)} conversations for user {user_id}")
            return result
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in list_conversations_for_user: {str(e)}")
            raise

    @staticmethod
    def list_conversations_anonymous() -> List[Dict[str, Any]]:
        app_logger.log_info("[ConversationManager] Starting list_conversations_anonymous")
        try:
            conversations = []
            for fname in os.listdir(CONV_DATA_DIR):
                if fname.endswith('.json'):
                    with open(os.path.join(CONV_DATA_DIR, fname), 'r') as f:
                        conv = json.load(f)
                        if not conv.get('user_id') and not conv.get('deleted', False):
                            conversations.append({
                                'conversation_id': conv['conversation_id'],
                                'created_at': conv['created_at'],
                                'updated_at': conv['updated_at'],
                                'last_message_preview': conv.get('last_message_preview', ''),
                                'is_active': conv.get('is_active', True)
                            })
            result = sorted(conversations, key=lambda x: x['updated_at'], reverse=True)
            app_logger.log_info(f"[ConversationManager] Successfully retrieved {len(result)} anonymous conversations")
            return result
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in list_conversations_anonymous: {str(e)}")
            raise

    @staticmethod
    def add_document_to_conversation(conversation_id: str, document_id: str, document_metadata: Dict[str, Any], user_id: str) -> bool:
        """Add a document reference to a conversation"""
        app_logger.log_info(f"[ConversationManager] Starting add_document_to_conversation for conversation_id: {conversation_id}, document_id: {document_id}, user_id: {user_id}")
        try:
            path = _conv_path(conversation_id)
            if not os.path.exists(path):
                return False
                
            with open(path, 'r') as f:
                conversation = json.load(f)
            
            if 'documents' not in conversation:
                conversation['documents'] = []
            
            # Check if document already exists
            if any(doc['document_id'] == document_id for doc in conversation['documents']):
                return False
                
            doc_entry = {
                'document_id': document_id,
                'filename': document_metadata.get('filename', ''),
                'file_type': document_metadata.get('file_type', ''),
                'added_at': _now(),
                'added_by': user_id
            }
            
            conversation['documents'].append(doc_entry)
            conversation['updated_at'] = _now()
            
            with open(path, 'w') as f:
                json.dump(conversation, f, indent=2)

            app_logger.log_info(f"[ConversationManager] Successfully added document {document_id} to conversation {conversation_id}")
            return True
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in add_document_to_conversation: {str(e)}")
            return False

    @staticmethod
    def remove_document_from_conversation(conversation_id: str, document_id: str, cleanup_references: bool = True) -> int:
        """Remove a document from conversation and optionally clean up references.
        Returns the number of references cleaned up."""
        app_logger.log_info(f"[ConversationManager] Starting remove_document_from_conversation for conversation_id: {conversation_id}, document_id: {document_id}, cleanup_references: {cleanup_references}")
        try:
            path = _conv_path(conversation_id)
            if not os.path.exists(path):
                return 0
                
            with open(path, 'r') as f:
                conversation = json.load(f)
            
            # Remove from documents list
            original_docs = conversation.get('documents', [])
            conversation['documents'] = [doc for doc in original_docs if doc['document_id'] != document_id]
            
            references_cleaned = 0
            if cleanup_references:
                # Clean up message attachments and sidebar_info
                for message in conversation.get('messages', []):
                    # Clean attachments
                    if 'attachments' in message and message['attachments']:
                        original_count = len(message['attachments'])
                        message['attachments'] = [
                            att for att in message['attachments'] 
                            if att.get('document_id') != document_id
                        ]
                        if len(message['attachments']) < original_count:
                            references_cleaned += 1
                    
                    # Clean sidebar_info
                    if 'sidebar_info' in message and message['sidebar_info']:
                        if isinstance(message['sidebar_info'], dict):
                            if message['sidebar_info'].get('document_id') == document_id:
                                message['sidebar_info'] = None
                                references_cleaned += 1
            
            conversation['updated_at'] = _now()
            
            with open(path, 'w') as f:
                json.dump(conversation, f, indent=2)

            app_logger.log_info(f"[ConversationManager] Successfully removed document {document_id} from conversation {conversation_id}, cleaned {references_cleaned} references")
            return references_cleaned
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in remove_document_from_conversation: {str(e)}")
            return 0

    @staticmethod
    def get_conversation_documents(conversation_id: str) -> List[Dict[str, Any]]:
        """Get all documents associated with a conversation"""
        app_logger.log_info(f"[ConversationManager] Starting get_conversation_documents for conversation_id: {conversation_id}")
        try:
            conversation = ConversationManager.get_conversation(conversation_id)
            documents = conversation.get('documents', [])
            app_logger.log_info(f"[ConversationManager] Successfully retrieved {len(documents)} documents for conversation {conversation_id}")
            return documents
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in get_conversation_documents: {str(e)}")
            return []

    @staticmethod
    def update_document_reference_in_messages(conversation_id: str, old_document_id: str, new_document_id: str) -> int:
        """Update document references in messages when a document ID changes.
        Returns the number of references updated."""
        app_logger.log_info(f"[ConversationManager] Starting update_document_reference_in_messages for conversation_id: {conversation_id}, old_document_id: {old_document_id}, new_document_id: {new_document_id}")
        try:
            path = _conv_path(conversation_id)
            if not os.path.exists(path):
                return 0
                
            with open(path, 'r') as f:
                conversation = json.load(f)
            
            references_updated = 0
            for message in conversation.get('messages', []):
                # Update attachments
                if 'attachments' in message and message['attachments']:
                    for attachment in message['attachments']:
                        if attachment.get('document_id') == old_document_id:
                            attachment['document_id'] = new_document_id
                            references_updated += 1
                
                # Update sidebar_info
                if 'sidebar_info' in message and message['sidebar_info']:
                    if isinstance(message['sidebar_info'], dict):
                        if message['sidebar_info'].get('document_id') == old_document_id:
                            message['sidebar_info']['document_id'] = new_document_id
                            references_updated += 1
            
            if references_updated > 0:
                conversation['updated_at'] = _now()
                with open(path, 'w') as f:
                    json.dump(conversation, f, indent=2)

            app_logger.log_info(f"[ConversationManager] Successfully updated {references_updated} document references in conversation {conversation_id}")
            return references_updated
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in update_document_reference_in_messages: {str(e)}")
            return 0 