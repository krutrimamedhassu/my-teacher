import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio
from app.core.response.generative_responder import GenerativeResponder
from app.logger.app_logger import app_logger


def _now():
    return datetime.utcnow().isoformat()


def _get_col():
    """Get the MongoDB conversations collection, reusing the existing db_manager connection."""
    from app.core.data.database import db_manager
    return db_manager.db['conversations']


class ConversationManager:

    @staticmethod
    def create_conversation(user_id: Optional[str] = None, username: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] create_conversation user_id={user_id}")
        try:
            conversation_id = str(uuid.uuid4())
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
            _get_col().insert_one({**conversation})
            app_logger.log_info(f"[ConversationManager] Created conversation {conversation_id}")
            return conversation
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in create_conversation: {e}")
            raise

    @staticmethod
    def create_conversation_with_id(conversation_id: Optional[str] = None, user_id: Optional[str] = None, username: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] create_conversation_with_id conversation_id={conversation_id}")
        try:
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
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
            _get_col().insert_one({**conversation})
            app_logger.log_info(f"[ConversationManager] Created conversation with ID {conversation_id}")
            return conversation
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in create_conversation_with_id: {e}")
            raise

    @staticmethod
    def append_message(conversation_id: str, sender_id: Optional[str], sender_username: Optional[str], role: str, text: str, attachments: Optional[List[Any]] = None, sidebar_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] append_message conversation_id={conversation_id} role={role}")
        try:
            col = _get_col()
            conv = col.find_one({'conversation_id': conversation_id, 'deleted': False}, {'_id': 0})
            if not conv:
                raise FileNotFoundError('Conversation not found')

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
            if sidebar_info:
                message['sidebar_info'] = sidebar_info

            now = _now()
            set_fields = {
                'updated_at': now,
                'last_message_preview': text[:100]
            }

            # Auto-title on first message
            if len(conv.get('messages', [])) == 0:
                try:
                    async def _gen_title():
                        async with GenerativeResponder() as r:
                            return await r.generate_title(text)
                    try:
                        loop = asyncio.get_running_loop()
                        title = loop.run_until_complete(_gen_title())
                    except RuntimeError:
                        title = asyncio.run(_gen_title())
                    set_fields['title'] = title
                except Exception:
                    words = text.strip().split()
                    t = ' '.join(words[:4])
                    set_fields['title'] = t[:27] + '...' if len(t) > 30 else t

            col.update_one(
                {'conversation_id': conversation_id},
                {'$push': {'messages': message}, '$set': set_fields}
            )
            app_logger.log_info(f"[ConversationManager] Appended message to {conversation_id}")
            return message
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in append_message: {e}")
            raise

    @staticmethod
    def get_conversation(conversation_id: str) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] get_conversation {conversation_id}")
        try:
            conv = _get_col().find_one({'conversation_id': conversation_id, 'deleted': False}, {'_id': 0})
            if not conv:
                raise FileNotFoundError('Conversation not found')
            return conv
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in get_conversation: {e}")
            raise

    @staticmethod
    def edit_conversation(conversation_id: str, title: Optional[str] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
        app_logger.log_info(f"[ConversationManager] edit_conversation {conversation_id}")
        try:
            col = _get_col()
            conv = col.find_one({'conversation_id': conversation_id, 'deleted': False}, {'_id': 0})
            if not conv:
                raise FileNotFoundError('Conversation not found')
            set_fields: Dict[str, Any] = {'updated_at': _now()}
            if title is not None:
                set_fields['title'] = title
            if is_active is not None:
                set_fields['is_active'] = is_active
            col.update_one({'conversation_id': conversation_id}, {'$set': set_fields})
            conv.update(set_fields)
            return conv
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in edit_conversation: {e}")
            raise

    @staticmethod
    def delete_conversation(conversation_id: str) -> Dict[str, Any]:
        """Soft-delete a conversation."""
        app_logger.log_info(f"[ConversationManager] delete_conversation {conversation_id}")
        try:
            col = _get_col()
            conv = col.find_one({'conversation_id': conversation_id}, {'_id': 0})
            if not conv:
                raise FileNotFoundError('Conversation not found')
            set_fields = {'deleted': True, 'is_active': False, 'updated_at': _now()}
            col.update_one({'conversation_id': conversation_id}, {'$set': set_fields})
            conv.update(set_fields)
            return conv
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in delete_conversation: {e}")
            raise

    @staticmethod
    def list_conversations_for_user(user_id: str) -> List[Dict[str, Any]]:
        app_logger.log_info(f"[ConversationManager] list_conversations_for_user {user_id}")
        try:
            cursor = _get_col().find(
                {'user_id': user_id, 'deleted': False},
                {'_id': 0, 'conversation_id': 1, 'title': 1, 'created_at': 1, 'updated_at': 1, 'last_message_preview': 1, 'is_active': 1}
            ).sort('updated_at', -1)
            result = list(cursor)
            app_logger.log_info(f"[ConversationManager] Found {len(result)} conversations for user {user_id}")
            return result
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in list_conversations_for_user: {e}")
            raise

    @staticmethod
    def list_conversations_anonymous() -> List[Dict[str, Any]]:
        app_logger.log_info("[ConversationManager] list_conversations_anonymous")
        try:
            cursor = _get_col().find(
                {'user_id': None, 'deleted': False},
                {'_id': 0, 'conversation_id': 1, 'created_at': 1, 'updated_at': 1, 'last_message_preview': 1, 'is_active': 1}
            ).sort('updated_at', -1)
            result = list(cursor)
            app_logger.log_info(f"[ConversationManager] Found {len(result)} anonymous conversations")
            return result
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in list_conversations_anonymous: {e}")
            raise

    @staticmethod
    def delete_empty_conversations_for_user(user_id: str) -> Dict[str, Any]:
        """Hard-delete all conversations with zero messages for a user."""
        app_logger.log_info(f"[ConversationManager] delete_empty_conversations_for_user {user_id}")
        try:
            col = _get_col()
            result = col.delete_many({'user_id': user_id, 'deleted': False, 'messages': {'$size': 0}})
            deleted_count = result.deleted_count
            app_logger.log_info(f"[ConversationManager] Deleted {deleted_count} empty conversations for user {user_id}")
            return {'deleted_count': deleted_count}
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in delete_empty_conversations_for_user: {e}")
            raise

    @staticmethod
    def add_document_to_conversation(conversation_id: str, document_id: str, document_metadata: Dict[str, Any], user_id: str) -> bool:
        app_logger.log_info(f"[ConversationManager] add_document_to_conversation {conversation_id} doc={document_id}")
        try:
            col = _get_col()
            conv = col.find_one({'conversation_id': conversation_id}, {'_id': 0, 'documents': 1})
            if not conv:
                return False
            if any(d['document_id'] == document_id for d in conv.get('documents', [])):
                return False
            doc_entry = {
                'document_id': document_id,
                'filename': document_metadata.get('filename', ''),
                'file_type': document_metadata.get('file_type', ''),
                'added_at': _now(),
                'added_by': user_id
            }
            col.update_one(
                {'conversation_id': conversation_id},
                {'$push': {'documents': doc_entry}, '$set': {'updated_at': _now()}}
            )
            return True
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in add_document_to_conversation: {e}")
            return False

    @staticmethod
    def remove_document_from_conversation(conversation_id: str, document_id: str, cleanup_references: bool = True) -> int:
        app_logger.log_info(f"[ConversationManager] remove_document_from_conversation {conversation_id} doc={document_id}")
        try:
            col = _get_col()
            conv = col.find_one({'conversation_id': conversation_id}, {'_id': 0})
            if not conv:
                return 0

            references_cleaned = 0
            set_fields: Dict[str, Any] = {'updated_at': _now()}

            if cleanup_references:
                messages = conv.get('messages', [])
                for msg in messages:
                    if msg.get('attachments'):
                        orig = len(msg['attachments'])
                        msg['attachments'] = [a for a in msg['attachments'] if a.get('document_id') != document_id]
                        if len(msg['attachments']) < orig:
                            references_cleaned += 1
                    if isinstance(msg.get('sidebar_info'), dict) and msg['sidebar_info'].get('document_id') == document_id:
                        msg['sidebar_info'] = None
                        references_cleaned += 1
                set_fields['messages'] = messages

            col.update_one(
                {'conversation_id': conversation_id},
                {'$pull': {'documents': {'document_id': document_id}}, '$set': set_fields}
            )
            return references_cleaned
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in remove_document_from_conversation: {e}")
            return 0

    @staticmethod
    def get_conversation_documents(conversation_id: str) -> List[Dict[str, Any]]:
        try:
            conv = ConversationManager.get_conversation(conversation_id)
            return conv.get('documents', [])
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in get_conversation_documents: {e}")
            return []

    @staticmethod
    def update_document_reference_in_messages(conversation_id: str, old_document_id: str, new_document_id: str) -> int:
        app_logger.log_info(f"[ConversationManager] update_document_reference_in_messages {conversation_id}")
        try:
            col = _get_col()
            conv = col.find_one({'conversation_id': conversation_id}, {'_id': 0})
            if not conv:
                return 0

            references_updated = 0
            messages = conv.get('messages', [])
            for msg in messages:
                for att in msg.get('attachments', []):
                    if att.get('document_id') == old_document_id:
                        att['document_id'] = new_document_id
                        references_updated += 1
                if isinstance(msg.get('sidebar_info'), dict) and msg['sidebar_info'].get('document_id') == old_document_id:
                    msg['sidebar_info']['document_id'] = new_document_id
                    references_updated += 1

            if references_updated > 0:
                col.update_one(
                    {'conversation_id': conversation_id},
                    {'$set': {'messages': messages, 'updated_at': _now()}}
                )
            return references_updated
        except Exception as e:
            app_logger.log_error(f"[ConversationManager] Error in update_document_reference_in_messages: {e}")
            return 0
