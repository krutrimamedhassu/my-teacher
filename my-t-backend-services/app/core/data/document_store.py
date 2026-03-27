import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from app.core.config import settings
from app.logger.app_logger import app_logger


class DocumentStore:
    """
    MongoDB service for storing and retrieving document metadata and content.
    """
    
    def __init__(self, mongodb_uri: str = settings.MONGODB_URI):
        """
        Initialize MongoDB connection.

        Args:
            mongodb_uri: MongoDB connection string
        """
        app_logger.log_info(f"[DocumentStore] Initializing DocumentStore")

        if not mongodb_uri:
            app_logger.log_error(f"[DocumentStore] MongoDB URI is required but not provided")
            raise ValueError("MongoDB URI is required")

        # Sanitize URI for logging (hide credentials)
        uri_preview = mongodb_uri.split('@')[-1] if '@' in mongodb_uri else mongodb_uri[:50] + '...'
        app_logger.log_debug(f"[DocumentStore] Connecting to MongoDB: {uri_preview}")
        app_logger.log_debug(f"[DocumentStore] Using database: {settings.MONGODB_TEST_DB}")

        try:
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[settings.MONGODB_TEST_DB]
            self.documents = self.db.documents
            self.chunks = self.db.document_chunks

            app_logger.log_debug(f"[DocumentStore] MongoDB client initialized successfully")
            app_logger.log_debug(f"[DocumentStore] Collections initialized: documents, document_chunks")

            # Create indexes for better performance
            app_logger.log_debug(f"[DocumentStore] Creating database indexes")
            self._create_indexes()

            app_logger.log_info(f"[DocumentStore] DocumentStore initialized successfully")
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Error initializing DocumentStore: {str(e)}")
            raise
        
    def _create_indexes(self):
        """Create database indexes for better query performance."""
        app_logger.log_debug(f"[DocumentStore] Starting index creation process")

        try:
            # Index for document metadata
            app_logger.log_debug(f"[DocumentStore] Creating document metadata indexes")
            self.documents.create_index([("filename", 1)])
            self.documents.create_index([("upload_date", -1)])
            self.documents.create_index([("file_type", 1)])
            app_logger.log_debug(f"[DocumentStore] Document metadata indexes created")

            # Index for document chunks
            app_logger.log_debug(f"[DocumentStore] Creating document chunks indexes")
            self.chunks.create_index([("document_id", 1)])
            self.chunks.create_index([("chunk_index", 1)])
            app_logger.log_debug(f"[DocumentStore] Document chunks indexes created")

            # Text index for search functionality
            try:
                app_logger.log_debug(f"[DocumentStore] Creating text search index")
                self.chunks.create_index([("content", "text")])
                app_logger.log_info("[DocumentStore] Text index created for search")
            except Exception as e:
                app_logger.log_warning(f"[DocumentStore] Text index creation failed (may already exist): {str(e)}")

            app_logger.log_info("[DocumentStore] MongoDB indexes created successfully")
        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Failed to create indexes: {str(e)}")
            raise
    
    async def store_document(
        self,
        filename: str,
        file_type: str,
        file_size: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store document metadata and content in MongoDB.

        Args:
            filename: Original filename
            file_type: File extension/type
            file_size: File size in bytes
            content: Extracted text content
            metadata: Additional metadata

        Returns:
            str: Document ID
        """
        content_length = len(content)
        app_logger.log_info(f"[DocumentStore] Entering store_document - filename: {filename}, type: {file_type}")
        app_logger.log_debug(f"[DocumentStore] File details - size: {file_size} bytes, content_length: {content_length} chars")
        app_logger.log_debug(f"[DocumentStore] Metadata keys: {list(metadata.keys()) if metadata else 'none'}")

        try:
            # Store document metadata
            doc_data = {
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size,
                "upload_date": datetime.utcnow(),
                "metadata": metadata or {},
                "total_chunks": 0
            }

            app_logger.log_debug(f"[DocumentStore] Inserting document metadata to MongoDB")
            result = self.documents.insert_one(doc_data)
            document_id = str(result.inserted_id)
            app_logger.log_debug(f"[DocumentStore] Document metadata stored with ID: {document_id}")

            # Split content into chunks and store
            app_logger.log_debug(f"[DocumentStore] Splitting content into chunks")
            chunks = self._split_content(content)
            app_logger.log_debug(f"[DocumentStore] Content split into {len(chunks)} chunks")

            chunk_docs = []
            for i, chunk in enumerate(chunks):
                chunk_doc = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk,
                    "created_at": datetime.utcnow()
                }
                chunk_docs.append(chunk_doc)

            if chunk_docs:
                app_logger.log_debug(f"[DocumentStore] Inserting {len(chunk_docs)} chunks to MongoDB")
                self.chunks.insert_many(chunk_docs)

                # Update total chunks count
                app_logger.log_debug(f"[DocumentStore] Updating document with total chunks count: {len(chunks)}")
                self.documents.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"total_chunks": len(chunks)}}
                )
            else:
                app_logger.log_warning(f"[DocumentStore] No chunks created for document: {filename}")

            app_logger.log_info(f"[DocumentStore] Document stored successfully - filename: {filename}, ID: {document_id}, chunks: {len(chunks)}")
            return document_id

        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Failed to store document {filename}: {str(e)}")
            raise
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Unexpected error storing document {filename}: {str(e)}")
            raise
    
    def _split_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """
        Split content into chunks for better processing.

        Args:
            content: Text content to split
            chunk_size: Maximum size of each chunk

        Returns:
            List[str]: List of content chunks
        """
        content_length = len(content)
        app_logger.log_debug(f"[DocumentStore] Splitting content - length: {content_length}, chunk_size: {chunk_size}")

        if len(content) <= chunk_size:
            app_logger.log_debug(f"[DocumentStore] Content fits in single chunk")
            return [content]

        chunks = []
        current_chunk = ""

        # Split by sentences first, then by words if needed
        sentences = content.split('. ')
        app_logger.log_debug(f"[DocumentStore] Found {len(sentences)} sentences to process")

        for i, sentence in enumerate(sentences):
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    app_logger.log_debug(f"[DocumentStore] Created chunk {len(chunks)}, length: {len(current_chunk)}")
                current_chunk = sentence + '. '

        if current_chunk:
            chunks.append(current_chunk.strip())
            app_logger.log_debug(f"[DocumentStore] Created final chunk {len(chunks)}, length: {len(current_chunk)}")

        app_logger.log_debug(f"[DocumentStore] Content split complete - created {len(chunks)} chunks")
        return chunks
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document metadata by ID.

        Args:
            document_id: Document ID

        Returns:
            Optional[Dict]: Document metadata or None if not found
        """
        app_logger.log_debug(f"[DocumentStore] Entering get_document for ID: {document_id}")

        try:
            # Convert string ID to ObjectId for MongoDB query
            app_logger.log_debug(f"[DocumentStore] Converting string ID to ObjectId: {document_id}")
            object_id = ObjectId(document_id)

            app_logger.log_debug(f"[DocumentStore] Querying documents collection for ID: {document_id}")
            doc = self.documents.find_one({"_id": object_id})

            if doc:
                doc["_id"] = str(doc["_id"])
                app_logger.log_info(f"[DocumentStore] Document retrieved successfully - ID: {document_id}, filename: {doc.get('filename')}")
                app_logger.log_debug(f"[DocumentStore] Document details - type: {doc.get('file_type')}, size: {doc.get('file_size')}, chunks: {doc.get('total_chunks')}")
                return doc
            else:
                app_logger.log_warning(f"[DocumentStore] Document not found for ID: {document_id}")
                return None

        except ValueError as e:
            app_logger.log_warning(f"[DocumentStore] Invalid document ID format: {document_id} - {str(e)}")
            return None
        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Database error retrieving document {document_id}: {str(e)}")
            return None
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Unexpected error retrieving document {document_id}: {str(e)}")
            return None
    
    async def get_document_content(self, document_id: str) -> Optional[str]:
        """
        Retrieve full document content by ID.

        Args:
            document_id: Document ID

        Returns:
            Optional[str]: Full document content or None if not found
        """
        app_logger.log_debug(f"[DocumentStore] Entering get_document_content for ID: {document_id}")

        try:
            app_logger.log_debug(f"[DocumentStore] Querying chunks for document: {document_id}")
            chunks = self.chunks.find(
                {"document_id": document_id}
            ).sort("chunk_index", 1)

            content = ""
            chunk_count = 0
            for chunk in chunks:
                content += chunk["content"] + " "
                chunk_count += 1

            app_logger.log_debug(f"[DocumentStore] Retrieved {chunk_count} chunks for document: {document_id}")

            if content:
                final_content = content.strip()
                content_length = len(final_content)
                app_logger.log_info(f"[DocumentStore] Document content retrieved successfully - ID: {document_id}, length: {content_length} chars, chunks: {chunk_count}")
                return final_content
            else:
                app_logger.log_warning(f"[DocumentStore] No content found for document: {document_id}")
                return None

        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Database error retrieving content for document {document_id}: {str(e)}")
            return None
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Unexpected error retrieving content for document {document_id}: {str(e)}")
            return None
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents by content using text search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List[Dict]: List of matching documents with relevance scores
        """
        query_preview = query[:50] + '...' if len(query) > 50 else query
        app_logger.log_info(f"[DocumentStore] Entering search_documents - query: '{query_preview}', limit: {limit}")

        try:
            # Simple text search using MongoDB text index
            app_logger.log_debug(f"[DocumentStore] Performing MongoDB text search")
            search_results = self.chunks.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)

            # Group results by document_id
            document_scores = {}
            document_chunks = {}
            total_matches = 0

            for result in search_results:
                doc_id = result["document_id"]
                score = result.get("score", 0)
                content = result.get("content", "")
                total_matches += 1

                if doc_id not in document_scores:
                    document_scores[doc_id] = score
                    document_chunks[doc_id] = [content]
                else:
                    document_scores[doc_id] = max(document_scores[doc_id], score)
                    document_chunks[doc_id].append(content)

            app_logger.log_debug(f"[DocumentStore] Text search found {total_matches} matching chunks across {len(document_scores)} documents")

            # Get document metadata for each found document
            formatted_results = []
            for doc_id, score in sorted(document_scores.items(), key=lambda x: x[1], reverse=True):
                app_logger.log_debug(f"[DocumentStore] Getting metadata for document: {doc_id}, score: {score:.2f}")
                doc_metadata = await self.get_document(doc_id)
                if doc_metadata:
                    result_item = {
                        "document": doc_metadata,
                        "relevance_score": score,
                        "matched_content": document_chunks[doc_id][:3]  # Top 3 matching chunks
                    }
                    formatted_results.append(result_item)

            app_logger.log_info(f"[DocumentStore] Search completed successfully - query: '{query_preview}', results: {len(formatted_results)}")
            return formatted_results

        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Text search failed for query '{query_preview}': {str(e)}")
            # Fallback to simple keyword search
            app_logger.log_info(f"[DocumentStore] Falling back to keyword search")
            return await self._fallback_search(query, limit)
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Unexpected error in search for query '{query_preview}': {str(e)}")
            return []
    
    async def _fallback_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fallback search method using simple keyword matching.
        """
        query_preview = query[:50] + '...' if len(query) > 50 else query
        app_logger.log_debug(f"[DocumentStore] Starting fallback search for query: '{query_preview}'")

        try:
            # Simple keyword search
            query_words = query.lower().split()
            app_logger.log_debug(f"[DocumentStore] Search keywords: {query_words}")

            all_chunks = self.chunks.find()
            document_scores = {}
            document_chunks = {}
            chunks_processed = 0

            for chunk in all_chunks:
                doc_id = chunk["document_id"]
                content = chunk.get("content", "").lower()
                chunks_processed += 1

                # Calculate simple relevance score
                score = sum(1 for word in query_words if word in content)

                if score > 0:
                    if doc_id not in document_scores:
                        document_scores[doc_id] = score
                        document_chunks[doc_id] = [chunk.get("content", "")]
                    else:
                        document_scores[doc_id] += score
                        document_chunks[doc_id].append(chunk.get("content", ""))

            app_logger.log_debug(f"[DocumentStore] Fallback search processed {chunks_processed} chunks, found {len(document_scores)} matching documents")

            # Get document metadata and format results
            formatted_results = []
            for doc_id, score in sorted(document_scores.items(), key=lambda x: x[1], reverse=True)[:limit]:
                app_logger.log_debug(f"[DocumentStore] Processing fallback result - doc_id: {doc_id}, score: {score}")
                doc_metadata = await self.get_document(doc_id)
                if doc_metadata:
                    formatted_results.append({
                        "document": doc_metadata,
                        "relevance_score": score,
                        "matched_content": document_chunks[doc_id][:3]
                    })

            app_logger.log_info(f"[DocumentStore] Fallback search completed - query: '{query_preview}', results: {len(formatted_results)}")
            return formatted_results

        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Fallback search database error for query '{query_preview}': {str(e)}")
            return []
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Unexpected error in fallback search for query '{query_preview}': {str(e)}")
            return []
    
    async def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all documents with metadata.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List[Dict]: List of document metadata
        """
        app_logger.log_debug(f"[DocumentStore] Entering list_documents with limit: {limit}")

        try:
            app_logger.log_debug(f"[DocumentStore] Querying documents collection, sorted by upload_date desc")
            docs = self.documents.find().sort("upload_date", -1).limit(limit)

            result = []
            for doc in docs:
                doc["_id"] = str(doc["_id"])
                result.append(doc)

            app_logger.log_info(f"[DocumentStore] Listed {len(result)} documents (limit: {limit})")
            if result:
                app_logger.log_debug(f"[DocumentStore] Document types in results: {set(doc.get('file_type') for doc in result)}")

            return result

        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Database error listing documents: {str(e)}")
            return []
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Unexpected error listing documents: {str(e)}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document and all its chunks.

        Args:
            document_id: Document ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        app_logger.log_info(f"[DocumentStore] Entering delete_document for ID: {document_id}")

        try:
            # First, get document info for logging
            try:
                doc_info = await self.get_document(document_id)
                if doc_info:
                    app_logger.log_debug(f"[DocumentStore] Document to delete - filename: {doc_info.get('filename')}, type: {doc_info.get('file_type')}, chunks: {doc_info.get('total_chunks')}")
            except Exception as e:
                app_logger.log_debug(f"[DocumentStore] Could not get document info before deletion: {str(e)}")

            # Delete chunks first
            app_logger.log_debug(f"[DocumentStore] Deleting chunks for document: {document_id}")
            chunks_result = self.chunks.delete_many({"document_id": document_id})
            deleted_chunks = chunks_result.deleted_count
            app_logger.log_debug(f"[DocumentStore] Deleted {deleted_chunks} chunks")

            # Delete document metadata
            app_logger.log_debug(f"[DocumentStore] Deleting document metadata for ID: {document_id}")
            object_id = ObjectId(document_id)
            result = self.documents.delete_one({"_id": object_id})

            success = result.deleted_count > 0
            if success:
                app_logger.log_info(f"[DocumentStore] Document deleted successfully - ID: {document_id}, chunks deleted: {deleted_chunks}")
            else:
                app_logger.log_warning(f"[DocumentStore] Document not found for deletion: {document_id} (but {deleted_chunks} orphaned chunks were deleted)")

            return success

        except ValueError as e:
            app_logger.log_warning(f"[DocumentStore] Invalid document ID format for deletion: {document_id} - {str(e)}")
            return False
        except PyMongoError as e:
            app_logger.log_error(f"[DocumentStore] Database error deleting document {document_id}: {str(e)}")
            return False
        except Exception as e:
            app_logger.log_error(f"[DocumentStore] Unexpected error deleting document {document_id}: {str(e)}")
            return False
    
    def close(self):
        """Close MongoDB connection."""
        app_logger.log_info(f"[DocumentStore] Closing MongoDB connection")
        if self.client:
            try:
                self.client.close()
                app_logger.log_info(f"[DocumentStore] MongoDB connection closed successfully")
            except Exception as e:
                app_logger.log_warning(f"[DocumentStore] Error closing MongoDB connection: {str(e)}")
        else:
            app_logger.log_debug(f"[DocumentStore] No MongoDB client to close")


# Global document store instance
document_store = DocumentStore() 