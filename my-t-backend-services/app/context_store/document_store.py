"""
Document storage backed by MongoDB.
Uses the shared mongo_client instead of opening its own connection.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo.errors import PyMongoError
from bson import ObjectId
from app.context_store.mongo_client import get_db
from app.logger.app_logger import app_logger


class DocumentStore:
    """MongoDB service for storing and retrieving document metadata and content."""

    def __init__(self):
        app_logger.log_info("[DocumentStore] Initializing DocumentStore")
        db = get_db()
        self.documents = db.documents
        self.chunks = db.document_chunks
        self._create_indexes()
        app_logger.log_info("[DocumentStore] DocumentStore initialized successfully")

    def _create_indexes(self):
        try:
            self.documents.create_index([("filename", 1)])
            self.documents.create_index([("upload_date", -1)])
            self.documents.create_index([("file_type", 1)])
            self.chunks.create_index([("document_id", 1)])
            self.chunks.create_index([("chunk_index", 1)])
            try:
                self.chunks.create_index([("content", "text")])
            except Exception:
                pass
            app_logger.log_info("[DocumentStore] Indexes created")
        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Failed to create indexes: {e}")
            raise

    async def store_document(self, filename: str, file_type: str, file_size: int, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        app_logger.log_info(f"[DocumentStore] store_document filename={filename}")
        try:
            doc_data = {
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size,
                "upload_date": datetime.utcnow(),
                "metadata": metadata or {},
                "total_chunks": 0
            }
            result = self.documents.insert_one(doc_data)
            document_id = str(result.inserted_id)

            chunks = self._split_content(content)
            if chunks:
                chunk_docs = [
                    {"document_id": document_id, "chunk_index": i, "content": chunk, "created_at": datetime.utcnow()}
                    for i, chunk in enumerate(chunks)
                ]
                self.chunks.insert_many(chunk_docs)
                self.documents.update_one({"_id": result.inserted_id}, {"$set": {"total_chunks": len(chunks)}})

            app_logger.log_info(f"[DocumentStore] Stored document {document_id} with {len(chunks)} chunks")
            return document_id
        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Failed to store document {filename}: {e}")
            raise

    def _split_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        if len(content) <= chunk_size:
            return [content]
        chunks = []
        current_chunk = ""
        for sentence in content.split('. '):
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc = self.documents.find_one({"_id": ObjectId(document_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except (ValueError, PyMongoError) as e:
            app_logger.log_warning(f"[DocumentStore] get_document error for {document_id}: {e}")
            return None

    async def get_document_content(self, document_id: str) -> Optional[str]:
        try:
            chunks = self.chunks.find({"document_id": document_id}).sort("chunk_index", 1)
            content = " ".join(c["content"] for c in chunks)
            return content.strip() or None
        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] get_document_content error for {document_id}: {e}")
            return None

    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            search_results = self.chunks.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)

            document_scores: Dict[str, float] = {}
            document_chunks: Dict[str, List[str]] = {}
            for result in search_results:
                doc_id = result["document_id"]
                score = result.get("score", 0)
                document_scores[doc_id] = max(document_scores.get(doc_id, 0), score)
                document_chunks.setdefault(doc_id, []).append(result.get("content", ""))

            formatted = []
            for doc_id, score in sorted(document_scores.items(), key=lambda x: x[1], reverse=True):
                meta = await self.get_document(doc_id)
                if meta:
                    formatted.append({"document": meta, "relevance_score": score, "matched_content": document_chunks[doc_id][:3]})
            return formatted
        except PyMongoError:
            return await self._fallback_search(query, limit)

    async def _fallback_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            words = query.lower().split()
            document_scores: Dict[str, int] = {}
            document_chunks: Dict[str, List[str]] = {}
            for chunk in self.chunks.find():
                doc_id = chunk["document_id"]
                content = chunk.get("content", "").lower()
                score = sum(1 for w in words if w in content)
                if score > 0:
                    document_scores[doc_id] = document_scores.get(doc_id, 0) + score
                    document_chunks.setdefault(doc_id, []).append(chunk.get("content", ""))
            formatted = []
            for doc_id, score in sorted(document_scores.items(), key=lambda x: x[1], reverse=True)[:limit]:
                meta = await self.get_document(doc_id)
                if meta:
                    formatted.append({"document": meta, "relevance_score": score, "matched_content": document_chunks[doc_id][:3]})
            return formatted
        except Exception:
            return []

    async def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            docs = self.documents.find().sort("upload_date", -1).limit(limit)
            result = []
            for doc in docs:
                doc["_id"] = str(doc["_id"])
                result.append(doc)
            return result
        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] list_documents error: {e}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        app_logger.log_info(f"[DocumentStore] delete_document {document_id}")
        try:
            self.chunks.delete_many({"document_id": document_id})
            result = self.documents.delete_one({"_id": ObjectId(document_id)})
            return result.deleted_count > 0
        except (ValueError, PyMongoError) as e:
            app_logger.log_error(f"[DocumentStore] delete_document error for {document_id}: {e}")
            return False


# Global instance
document_store = DocumentStore()
