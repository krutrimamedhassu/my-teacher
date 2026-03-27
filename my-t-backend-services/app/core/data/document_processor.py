import io
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Document processing libraries
import PyPDF2
from docx import Document
from bs4 import BeautifulSoup
import re

from app.core.config import settings
from app.logger.app_logger import app_logger


class DocumentProcessor:
    """
    Handles document processing and text extraction from various file types.
    """
    
    def __init__(self):
        """Initialize the document processor."""
        app_logger.log_info(f"[DocumentProcessor] Initializing DocumentProcessor")

        self.supported_types = {
            'pdf': self._extract_pdf_text,
            'docx': self._extract_docx_text,
            'txt': self._extract_txt_text,
            'html': self._extract_html_text,
            'htm': self._extract_html_text
        }

        app_logger.log_debug(f"[DocumentProcessor] Supported file types: {list(self.supported_types.keys())}")
        app_logger.log_info(f"[DocumentProcessor] DocumentProcessor initialized successfully")
    
    def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process a document and extract its content and metadata.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename

        Returns:
            Dict containing extracted text, metadata, and processing info
        """
        file_size = len(file_content)
        app_logger.log_info(f"[DocumentProcessor] Entering process_document - filename: {filename}, size: {file_size} bytes")

        try:
            # Get file extension
            file_ext = self._get_file_extension(filename)
            app_logger.log_debug(f"[DocumentProcessor] Detected file extension: {file_ext}")

            if file_ext not in self.supported_types:
                app_logger.log_error(f"[DocumentProcessor] Unsupported file type: {file_ext} for file: {filename}")
                app_logger.log_debug(f"[DocumentProcessor] Supported types: {list(self.supported_types.keys())}")
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Check file size
            max_size_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
            if file_size > max_size_bytes:
                app_logger.log_error(f"[DocumentProcessor] File too large - size: {file_size} bytes, max: {max_size_bytes} bytes ({settings.MAX_DOCUMENT_SIZE_MB}MB)")
                raise ValueError(f"File too large. Maximum size: {settings.MAX_DOCUMENT_SIZE_MB}MB")

            app_logger.log_debug(f"[DocumentProcessor] File size check passed - {file_size} bytes (<= {max_size_bytes} bytes)")

            # Extract text content
            app_logger.log_debug(f"[DocumentProcessor] Extracting text content using {file_ext} extractor")
            extractor = self.supported_types[file_ext]
            content = extractor(file_content)

            original_length = len(content)
            app_logger.log_debug(f"[DocumentProcessor] Raw content extracted - length: {original_length} chars")

            # Clean and normalize content
            app_logger.log_debug(f"[DocumentProcessor] Cleaning and normalizing content")
            cleaned_content = self._clean_content(content)

            cleaned_length = len(cleaned_content)
            app_logger.log_debug(f"[DocumentProcessor] Content cleaned - original: {original_length} chars, cleaned: {cleaned_length} chars")

            # Extract metadata
            app_logger.log_debug(f"[DocumentProcessor] Extracting document metadata")
            metadata = self._extract_metadata(content, filename, file_ext, file_size)

            word_count = len(cleaned_content.split())
            result = {
                "content": cleaned_content,
                "metadata": metadata,
                "file_type": file_ext,
                "file_size": file_size,
                "word_count": word_count,
                "char_count": cleaned_length
            }

            app_logger.log_info(f"[DocumentProcessor] Document processed successfully - filename: {filename}, type: {file_ext}, words: {word_count}, chars: {cleaned_length}")
            return result

        except ValueError as e:
            # Re-raise ValueError (validation errors) with original message
            app_logger.log_warning(f"[DocumentProcessor] Validation error processing {filename}: {str(e)}")
            raise
        except Exception as e:
            app_logger.log_error(f"[DocumentProcessor] Unexpected error processing document {filename}: {str(e)}")
            raise
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        extension = Path(filename).suffix.lower().lstrip('.')
        app_logger.log_debug(f"[DocumentProcessor] Extracted file extension '{extension}' from filename: {filename}")
        return extension
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        app_logger.log_debug(f"[DocumentProcessor] Starting PDF text extraction")

        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            total_pages = len(pdf_reader.pages)
            app_logger.log_debug(f"[DocumentProcessor] PDF contains {total_pages} pages")

            text_content = ""
            successful_pages = 0
            failed_pages = 0

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    app_logger.log_debug(f"[DocumentProcessor] Extracting text from PDF page {page_num + 1}/{total_pages}")
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text + "\n"
                        successful_pages += 1
                        app_logger.log_debug(f"[DocumentProcessor] Page {page_num + 1} extracted successfully - {len(page_text)} chars")
                    else:
                        app_logger.log_debug(f"[DocumentProcessor] Page {page_num + 1} contained no extractable text")
                        failed_pages += 1
                except Exception as e:
                    app_logger.log_warning(f"[DocumentProcessor] Failed to extract text from PDF page {page_num + 1}: {str(e)}")
                    failed_pages += 1
                    continue

            final_text = text_content.strip()
            app_logger.log_info(f"[DocumentProcessor] PDF text extraction completed - pages: {total_pages}, successful: {successful_pages}, failed: {failed_pages}, text_length: {len(final_text)}")
            return final_text

        except Exception as e:
            app_logger.log_error(f"[DocumentProcessor] Failed to extract PDF text: {str(e)}")
            raise
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            text_content = ""
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content += paragraph.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content += " | ".join(row_text) + "\n"
                text_content += "\n"  # Add spacing between tables
            
            return text_content.strip()
            
        except Exception as e:
            app_logger.log_error(f"Failed to extract DOCX text: {e}")
            raise
    
    def _extract_txt_text(self, file_content: bytes) -> str:
        """Extract text from TXT file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, use utf-8 with error handling
            return file_content.decode('utf-8', errors='ignore')
            
        except Exception as e:
            app_logger.log_error(f"Failed to extract TXT text: {e}")
            raise
    
    def _extract_html_text(self, file_content: bytes) -> str:
        """Extract text from HTML file."""
        try:
            # Decode HTML content
            html_content = file_content.decode('utf-8', errors='ignore')
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text_content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text_content.strip()
            
        except Exception as e:
            app_logger.log_error(f"Failed to extract HTML text: {e}")
            raise
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and normalize extracted content.
        
        Args:
            content: Raw extracted content
            
        Returns:
            str: Cleaned content
        """
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove excessive newlines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Remove special characters that might cause issues
        content = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']', '', content)
        
        # Normalize quotes
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")
        
        return content.strip()
    
    def _extract_metadata(self, content: str, filename: str, file_type: str, file_size: int) -> Dict[str, Any]:
        """
        Extract metadata from document content.
        
        Args:
            content: Document content
            filename: Original filename
            file_type: File type
            file_size: File size in bytes
            
        Returns:
            Dict: Extracted metadata
        """
        metadata = {
            "original_filename": filename,
            "file_type": file_type,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "word_count": len(content.split()),
            "char_count": len(content),
            "line_count": len(content.split('\n')),
            "estimated_pages": self._estimate_pages(content)
        }
        
        # Try to extract title from content, but prefer original filename
        extracted_title_from_content = self._extract_title(content)
        if extracted_title_from_content and len(extracted_title_from_content) > 5:
            metadata["content_based_title"] = extracted_title_from_content
        # Always use original filename as the primary title
        metadata["extracted_title"] = filename
        
        # Try to extract author from content
        author = self._extract_author(content)
        if author:
            metadata["extracted_author"] = author
        
        # Extract language hints
        language_hints = self._detect_language_hints(content)
        if language_hints:
            metadata["language_hints"] = language_hints
        
        return metadata
    
    def _estimate_pages(self, content: str) -> int:
        """Estimate number of pages based on content length."""
        # Rough estimate: 250 words per page
        word_count = len(content.split())
        return max(1, word_count // 250)
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Try to extract title from document content."""
        if not content:
            return None
        
        # Look for common title patterns
        lines = content.split('\n')
        
        # Check first few lines for potential title
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) < 200 and not line.isupper():
                # Check if it looks like a title (not too long, not all caps)
                if len(line.split()) <= 15 and not line.endswith('.'):
                    return line
        
        return None
    
    def _extract_author(self, content: str) -> Optional[str]:
        """Try to extract author from document content."""
        if not content:
            return None
        
        # Look for common author patterns
        author_patterns = [
            r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Author:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Written by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'©\s*\d{4}\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _detect_language_hints(self, content: str) -> Dict[str, float]:
        """Detect language hints based on character patterns."""
        if not content:
            return {}
        
        # Simple language detection based on character patterns
        total_chars = len(content)
        if total_chars == 0:
            return {}
        
        # Count specific characters for different languages
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', content))
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', content))
        
        hints = {}
        if english_chars > 0:
            hints["english"] = english_chars / total_chars
        if chinese_chars > 0:
            hints["chinese"] = chinese_chars / total_chars
        if japanese_chars > 0:
            hints["japanese"] = japanese_chars / total_chars
        if korean_chars > 0:
            hints["korean"] = korean_chars / total_chars
        
        return hints
    
    def get_supported_types(self) -> list:
        """Get list of supported file types."""
        return list(self.supported_types.keys())


# Global document processor instance
document_processor = DocumentProcessor() 