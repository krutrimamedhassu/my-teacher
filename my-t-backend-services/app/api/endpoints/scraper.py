from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional
from enum import Enum

from app.logger.app_logger import app_logger
from app.scraper.scraper_core import WebScraper
from app.core.auth.optional_auth import get_user_with_usage_tracking, create_limit_exceeded_response

router = APIRouter()


class ScrapingMode(str, Enum):
    """Enum for web scraping modes."""
    TEXT_ONLY = "text_only"
    HTML = "html"
    FULL = "full"


class ScrapingRequest(BaseModel):
    """Request model for web scraping."""
    url: HttpUrl
    mode: ScrapingMode = ScrapingMode.TEXT_ONLY
    extract_metadata: bool = True
    use_cache: bool = True


class ScrapingResponse(BaseModel):
    """Response model for web scraping."""
    url: str
    text: str
    title: Optional[str] = None
    metadata: Dict[str, Any]
    html: Optional[str] = None
    word_count: int
    links: Optional[List[str]] = None


@router.post(
    "",
    response_model=ScrapingResponse,
    status_code=status.HTTP_200_OK,
    summary="Scrape Web Content",
    description="Scrape content from a web page URL."
)
async def scrape_url(request: ScrapingRequest, http_request: Request) -> JSONResponse:
    """
    Scrape content from a URL.
    Supports both authenticated and unauthenticated users with usage tracking.
    
    Args:
        request: Request containing URL and scraping parameters
        http_request: HTTP request for authentication
        
    Returns:
        JSONResponse: Scraped content and metadata
    """
    try:
        # Authenticate and track usage
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "scraper"
        )
        
        app_logger.log_info(f"[Scraper] Scraping URL from {identifier}: {request.url} with mode: {request.mode}")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=limit_response,
                headers=response_headers
            )
        
        # Convert URL to string
        url = str(request.url)
        
        # Scrape the URL
        result = WebScraper.scrape_and_extract(url)
        
        # Prepare response based on mode
        response = {
            "url": url,
            "text": result["text"],
            "title": result["metadata"].get("title"),
            "metadata": result["metadata"],
            "word_count": len(result["text"].split())
        }
        
        # Include HTML if requested
        if request.mode in [ScrapingMode.HTML, ScrapingMode.FULL]:
            response["html"] = result["html"]
        
        # Extract links if in full mode
        if request.mode == ScrapingMode.FULL:
            # In a real implementation, we would extract links from the HTML
            # For now, we'll return mock data
            response["links"] = [
                f"{url}/page1",
                f"{url}/page2",
                f"{url}/page3"
            ]
        
        # Add usage warning for unauthenticated users
        if usage_info.get("tier") == "unauth":
            remaining = usage_info.get("remaining", 0)
            if remaining <= 2:
                response["usage_warning"] = {
                    "remaining_requests": remaining,
                    "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                    "upgrade_prompt": "Sign up for free to continue using our scraping service."
                }
        
        return JSONResponse(
            content=response,
            status_code=status.HTTP_200_OK,
            headers=response_headers
        )
    
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e
    except Exception as e:
        app_logger.log_error(f"[Scraper] Error scraping URL: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "scraping_failed", "message": f"Failed to scrape URL: {str(e)}"}
        )


@router.post(
    "/batch",
    response_model=List[ScrapingResponse],
    status_code=status.HTTP_200_OK,
    summary="Batch Scrape URLs",
    description="Scrape content from multiple URLs in a single request."
)
async def batch_scrape(
    urls: List[HttpUrl],
    http_request: Request,
    mode: ScrapingMode = ScrapingMode.TEXT_ONLY,
    extract_metadata: bool = True,
    use_cache: bool = True
) -> JSONResponse:
    """
    Scrape content from multiple URLs.
    Supports both authenticated and unauthenticated users with usage tracking.
    
    Args:
        urls: List of URLs to scrape
        http_request: HTTP request for authentication
        mode: Scraping mode
        extract_metadata: Whether to extract metadata
        use_cache: Whether to use cache
        
    Returns:
        JSONResponse: List of scraped content and metadata
    """
    try:
        # Authenticate and track usage
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "scraper_batch"
        )
        
        app_logger.log_info(f"[Scraper] Batch scraping {len(urls)} URLs from {identifier} with mode: {mode}")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=limit_response,
                headers=response_headers
            )
        
        # For batch scraping, limit the number of URLs for unauthenticated users
        if usage_info.get("tier") == "unauth" and len(urls) > 3:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "batch_limit_exceeded",
                    "message": "Anonymous users are limited to 3 URLs per batch request. Create a free account for higher limits.",
                    "max_urls": 3,
                    "provided_urls": len(urls),
                    "upgrade_message": "Sign up for free to batch scrape more URLs!"
                },
                headers=response_headers
            )
        
        results = []
        
        for url in urls:
            # Create a scraping request
            request = ScrapingRequest(
                url=url,
                mode=mode,
                extract_metadata=extract_metadata,
                use_cache=use_cache
            )
            
            # Scrape directly without calling the endpoint to avoid double auth
            try:
                url_str = str(url)
                result = WebScraper.scrape_and_extract(url_str)
                
                response = {
                    "url": url_str,
                    "text": result["text"],
                    "title": result["metadata"].get("title"),
                    "metadata": result["metadata"],
                    "word_count": len(result["text"].split())
                }
                
                # Include HTML if requested
                if request.mode in [ScrapingMode.HTML, ScrapingMode.FULL]:
                    response["html"] = result["html"]
                
                # Extract links if in full mode
                if request.mode == ScrapingMode.FULL:
                    response["links"] = [
                        f"{url_str}/page1",
                        f"{url_str}/page2",
                        f"{url_str}/page3"
                    ]
                
                results.append(response)
                
            except Exception as e:
                # Log the error but continue with other URLs
                app_logger.log_error(f"[Scraper] Error scraping URL {url}: {e}")
                results.append({
                    "url": str(url),
                    "text": f"Error: {str(e)}",
                    "metadata": {"error": str(e)},
                    "word_count": 0
                })
        
        # Add usage warning for unauthenticated users
        response_data = {"results": results}
        if usage_info.get("tier") == "unauth":
            remaining = usage_info.get("remaining", 0)
            if remaining <= 2:
                response_data["usage_warning"] = {
                    "remaining_requests": remaining,
                    "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                    "upgrade_prompt": "Sign up for free to continue using our scraping service."
                }
        
        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_200_OK,
            headers=response_headers
        )
    
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e
    except Exception as e:
        app_logger.log_error(f"[Scraper] Error in batch scraping: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "batch_scraping_failed", "message": f"Failed to perform batch scraping: {str(e)}"}
        )


@router.post(
    "/to-document",
    status_code=status.HTTP_201_CREATED,
    summary="Scrape URL to Document",
    description="Scrape a URL and save it as a document in the system."
)
async def scrape_to_document(
    url: HttpUrl,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scrape a URL and save it as a document.
    
    Args:
        url: URL to scrape
        title: Optional title for the document
        description: Optional description of the document
        tags: Optional comma-separated tags for the document
        
    Returns:
        dict: Created document information
    """
    app_logger.log_info(f"[Scraper] Scraping URL to document: {url}")
    
    try:
        # In a real implementation, this would:
        # 1. Scrape the URL
        # 2. Create a document from the scraped content
        # 3. Save the document
        
        # For now, we'll use the docs endpoint
        from app.api.endpoints.docs import process_url
        
        # Convert URL to string
        url_str = str(url)
        
        # Process the URL as a document
        return await process_url(
            url=url_str,
            title=title,
            description=description,
            tags=tags
        )
    
    except Exception as e:
        app_logger.log_error(f"[Scraper] Error scraping URL to document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape URL to document: {str(e)}"
        )