import sys
import os

# Ensure the package root (my-t-backend-services/) is on sys.path regardless of
# how or from where this file is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.api_v1 import api_router
from app.core.config import settings
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.logger.app_logger import app_logger
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware.logging_middleware import StructuredLoggingMiddleware
from app.core.clients import logfire_client


app = FastAPI(
    title=settings.TITLE_OF_THE_PROJECT,
    description=settings.DESCRIPTION_OF_THE_PROJECT,
    version=settings.VERSION
)

# Configure and instrument Logfire
logfire_client.configure_logfire()
logfire_client.instrument_fastapi(app)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

_LOCALHOST_ORIGINS = [
    "http://localhost:9100", "http://127.0.0.1:9100",
    "http://localhost:4000", "http://localhost:3000",
    "http://127.0.0.1:4000", "http://127.0.0.1:3000",
    "http://localhost:9000", "http://127.0.0.1:9000",
]

_cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS", "")
# Handle wildcard ("*" or '["*"]') — use ["*"] list which FastAPI CORS treats as allow-all
if _cors_origins_env.strip() in ("*", '["*"]', "['*']"):
    _cors_origins = ["*"]
elif _cors_origins_env:
    env_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
    # Always include localhost for local development, even when env var is set
    _cors_origins = list(dict.fromkeys(env_origins + _LOCALHOST_ORIGINS))
else:
    _cors_origins = _LOCALHOST_ORIGINS + ["https://my-teacher-ai.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
) # CORS middleware to allow cross-origin requests

# Mount static files
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

app.include_router(api_router, prefix=f"{settings.API_PREFIX}/v1")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My Teacher API</title>
  <link rel="icon" type="image/svg+xml" href="/static/open-book.svg" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0f0f13;
      color: #e2e2e8;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .container {
      text-align: center;
      padding: 48px 32px;
      max-width: 560px;
      width: 100%;
    }

    .badge {
      display: inline-block;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.35);
      color: #a5b4fc;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 4px 12px;
      border-radius: 999px;
      margin-bottom: 24px;
    }

    h1 {
      font-size: 40px;
      font-weight: 700;
      line-height: 1.15;
      background: linear-gradient(135deg, #e2e2e8 0%, #a5b4fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 16px;
    }

    p {
      color: #9292a0;
      font-size: 16px;
      line-height: 1.7;
      margin-bottom: 40px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: #fff;
      font-size: 15px;
      font-weight: 600;
      text-decoration: none;
      padding: 14px 32px;
      border-radius: 12px;
      transition: opacity 0.2s, transform 0.15s;
      box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
    }

    .btn:hover { opacity: 0.88; transform: translateY(-1px); }

    .btn svg { width: 18px; height: 18px; flex-shrink: 0; }

    .divider {
      margin: 40px auto;
      width: 48px;
      height: 2px;
      background: rgba(255,255,255,0.06);
      border-radius: 999px;
    }

    .endpoints {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .endpoint {
      display: flex;
      align-items: center;
      gap: 12px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 10px;
      padding: 12px 16px;
      text-align: left;
    }

    .method {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.06em;
      padding: 3px 8px;
      border-radius: 6px;
      flex-shrink: 0;
    }

    .get  { background: rgba(34,197,94,0.15);  color: #4ade80; }
    .post { background: rgba(59,130,246,0.15); color: #60a5fa; }

    .path {
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 13px;
      color: #c4c4d0;
    }

    .desc { font-size: 13px; color: #6b6b7e; margin-left: auto; }

    footer {
      margin-top: 48px;
      font-size: 12px;
      color: #444455;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="badge">REST API</div>
    <h1>My Teacher API</h1>
    <p>Backend services powering the My Teacher platform.<br/>Head to the docs to explore all available endpoints.</p>

    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a class="btn" href="/docs">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-3-3v6M4.5 19.5l15-15M19.5 4.5H13.5m6 0v6"/>
        </svg>
        Open API Docs
      </a>
      <a class="btn" href="https://my-teacher-ai.vercel.app" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#0ea5e9,#6366f1);">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"/>
        </svg>
        Go to App
      </a>
    </div>

    <div class="divider"></div>

    <div class="endpoints">
      <div class="endpoint">
        <span class="method get">GET</span>
        <span class="path">/docs</span>
        <span class="desc">Interactive Swagger UI</span>
      </div>
      <div class="endpoint">
        <span class="method get">GET</span>
        <span class="path">/redoc</span>
        <span class="desc">ReDoc reference</span>
      </div>
      <div class="endpoint">
        <span class="method post">POST</span>
        <span class="path">/api/v1/auth/login</span>
        <span class="desc">Authenticate</span>
      </div>
      <div class="endpoint">
        <span class="method post">POST</span>
        <span class="path">/api/v1/conversations/</span>
        <span class="desc">Start a conversation</span>
      </div>
      <div class="endpoint">
        <span class="method post">POST</span>
        <span class="path">/api/v1/chat/stream</span>
        <span class="desc">Streaming chat</span>
      </div>
    </div>

    <footer>My Teacher &mdash; API v1</footer>
  </div>
</body>
</html>""")

if __name__ == "__main__":
    try:
        port = settings.PORT
        host = "0.0.0.0"
        workers = os.cpu_count()  # Use the number of CPU cores as the number of workers

        app_logger.log_info(f"Starting server on {host}:{port}")
        app_logger.log_info(f"Workers configured: {settings.UVICORN_WORKER_COUNT}")
        app_logger.log_info(f"CPU cores available: {workers}")
        app_logger.log_info(f"Environment: {settings.ENVIRONMENT}")
        app_logger.log_info(f"Log level: info")

        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=settings.UVICORN_WORKER_COUNT,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        app_logger.log_info("Server shutdown requested by user")
    except Exception as e:
        app_logger.log_error("Failed to start the server", exc_info=e)
        raise e
    finally:
        app_logger.log_info("Server shutdown complete")

