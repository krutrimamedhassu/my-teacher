# My Teacher — Backend

FastAPI backend for the My Teacher AI study companion. Handles authentication, LLM interactions, document processing, speech, web scraping, and usage tracking.

---

## Tech Stack

| Layer | Library / Tool |
|---|---|
| Framework | FastAPI + Uvicorn (ASGI) |
| Language | Python 3.x |
| Database | MongoDB (PyMongo) |
| Authentication | JWT (PyJWT) + bcrypt (Passlib) |
| LLM | OpenAI API (sync + async clients) |
| Document Processing | PyPDF2, python-docx, BeautifulSoup4 |
| Speech | OpenAI Whisper (STT) + OpenAI TTS |
| Web Scraping | requests + BeautifulSoup4 |
| Validation | Pydantic + pydantic-settings |
| Logging | loguru + logfire |
| Real-time | WebSockets |

---

## Getting Started

### Prerequisites
- Python 3.10+
- MongoDB instance (local or Atlas)
- OpenAI API key

### Install & Run

```bash
cd my-t-backend-services

pip install -r requirements.txt

cp .env.example .env.local   # fill in values
export AI_ENV=local

python app/main.py
# Server: http://localhost:9150
# Swagger docs: http://localhost:9150/docs
```

---

## Environment Variables

Copy `.env.example` to `.env.local` (or `.env.dev`, `.env.prod`) and fill in:

```env
# Server
PORT=9150
API_PREFIX=/api
VERSION=0.1.0

# Project Info
PROJECT_NAME=AI Teacher
TITLE_OF_THE_PROJECT=AI Teacher API
DESCRIPTION_OF_THE_PROJECT=Backend API for AI Teacher

# LLM
OPENAI_API_KEY=sk-...
DEFAULT_MODEL=gpt-4.1
STREAMING_MODEL=            # optional override
MAX_TOKENS_GEN_TEXT=10000
STREAMING_CHUNK_SIZE=20

# Database
MONGODB_URI=mongodb+srv://...
MONGODB_TEST_DB=test_my_teacher_db

# Document Processing
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE_PATH=./vector_store
MAX_DOCUMENT_SIZE_MB=10
ALLOWED_DOCUMENT_TYPES=["pdf","txt","docx","html"]
DOCUMENT_STORE_INVOKER_URL=http://localhost:9150

# Speech
TTS_MODEL=tts-1
TTS_VOICE=alloy

# CORS
BACKEND_CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=info
LOGFIRE_TOKEN=              # optional
```

The environment file is selected by `AI_ENV`:

| `AI_ENV` | File loaded |
|---|---|
| `local` | `.env.local` |
| `dev` | `.env.dev` |
| `qa` | `.env.qa` |
| `prod` | `.env.prod` |

---

## Project Structure

```
app/
├── main.py                     # Uvicorn entrypoint, FastAPI app init, CORS
├── api/
│   ├── api_v1.py               # Registers all routers
│   └── endpoints/
│       ├── health.py
│       ├── auth.py
│       ├── conversations.py
│       ├── responder.py
│       ├── streaming.py
│       ├── websocket.py
│       ├── upload.py
│       ├── docs.py
│       ├── document_qa.py
│       ├── ai_keys.py
│       ├── flashcards.py
│       ├── breakdowns.py
│       ├── explanations.py
│       ├── key_concepts.py
│       ├── multiple_choice_questions.py
│       ├── question_paper.py
│       ├── study_plan.py
│       ├── visuals.py
│       ├── speech.py
│       ├── scraper.py
│       └── contact.py
│
├── core/
│   ├── config.py               # Pydantic settings (env vars)
│   ├── clients.py              # OpenAI + MongoDB client init
│   ├── prompts.py              # PROMPT_REGISTRY for all LLM tasks
│   ├── auth/
│   │   ├── auth_models.py      # Pydantic request/response models
│   │   ├── auth_utils.py       # JWT generation/verification, bcrypt
│   │   ├── auth_dependency.py  # get_current_user FastAPI dependency
│   │   ├── optional_auth.py    # Optional auth + usage tracking
│   │   ├── api_key_models.py   # API key models + tier limits
│   │   └── password_migration.py
│   ├── data/
│   │   ├── database.py         # DatabaseManager (MongoDB CRUD)
│   │   ├── doc_handler.py      # Document handlers
│   │   ├── document_processor.py
│   │   └── document_store.py
│   ├── middleware/
│   │   ├── logging_middleware.py   # Request logging + token counting
│   │   ├── api_key_middleware.py   # Rate limiting (IP-based for anon)
│   │   └── input_guards.py         # File validation, input sanitization
│   ├── response/
│   │   ├── generative_responder.py # Core LLM responder (async OpenAI)
│   │   ├── response_manager.py
│   │   └── context_manager.py      # Token counting + context trimming
│   ├── tools/
│   │   └── tool_registry.py        # Available AI tool definitions
│   └── utils/
│       └── endpoint_utils.py
│
├── conversations/
│   └── conversation_handler.py     # Conversation state management
├── scraper/
│   └── scraper_core.py             # Web scraping + text/metadata extraction
└── logger/
    └── app_logger.py               # Structured logging (loguru)
```

---

## API Endpoints

Base URL: `http://localhost:9150/api/v1`

### Authentication — `/auth`

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, returns JWT tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Get current user |
| PUT | `/auth/profile` | Update profile |
| PUT | `/auth/password` | Change password |
| PUT | `/auth/email` | Change email |
| POST | `/auth/profile-image` | Upload profile picture |

### Conversations — `/conversations`

| Method | Path | Description |
|---|---|---|
| POST | `/conversations/` | Create conversation |
| GET | `/conversations/{id}` | Get conversation |
| PATCH | `/conversations/{id}` | Edit conversation |
| DELETE | `/conversations/{id}` | Delete conversation |
| POST | `/conversations/{id}/messages` | Add message |
| GET | `/conversations/{id}/documents` | List documents |
| POST | `/conversations/{id}/documents` | Add document |

### AI Responder

| Method | Path | Description |
|---|---|---|
| POST | `/responder/` | Main AI teacher response |
| POST | `/streaming/` | Streaming response (SSE) |
| WS | `/ws/chat/{conversation_id}` | WebSocket real-time chat |

### Learning Tools

| Method | Path | Description |
|---|---|---|
| POST | `/flashcards/` | Generate flashcards |
| POST | `/key-concepts/extract-key-concepts` | Extract key concepts |
| POST | `/breakdowns/topic-breakdown/` | Topic breakdown |
| POST | `/explanations/` | Generate explanation |
| POST | `/multiple-choice-questions/` | Generate MCQs |
| POST | `/qa/` | Generate Q&A pairs |
| POST | `/study-plan/` | Create study plan |
| POST | `/visuals/` | Generate diagram/flowchart |
| POST | `/document-qa/` | Q&A from uploaded documents |

### Documents & Files

| Method | Path | Description |
|---|---|---|
| POST | `/upload/` | Upload single document |
| POST | `/upload/upload-multiple` | Upload multiple documents |
| GET | `/docs/{document_id}` | Get document |
| POST | `/docs/process-url` | Process URL as document |

### Speech

| Method | Path | Description |
|---|---|---|
| POST | `/speech/tts` | Text-to-speech (returns MP3) |
| POST | `/speech/tts/stream` | Streaming TTS |
| POST | `/speech/stt` | Speech-to-text (Whisper) |

### API Keys — `/api-keys`

| Method | Path | Description |
|---|---|---|
| POST | `/api-keys/create` | Create API key |
| GET | `/api-keys/` | List API keys |
| PUT | `/api-keys/{key_id}` | Update API key |
| DELETE | `/api-keys/{key_id}` | Delete API key |
| GET | `/api-keys/usage` | Usage statistics |
| GET | `/api-keys/tiers` | Tier information |

### Other

| Method | Path | Description |
|---|---|---|
| GET | `/health/` | Health check |
| POST | `/scraper/` | Scrape a URL |
| POST | `/contact/` | Submit contact message |

---

## Authentication Flow

1. User registers → password hashed with bcrypt → stored in MongoDB
2. Login returns `access_token` (short-lived) + `refresh_token`
3. All protected routes require `Authorization: Bearer <access_token>`
4. Expired tokens are refreshed via `POST /auth/refresh`
5. Unauthenticated users are tracked by IP with a **10 requests/month** limit

## User Tiers

| Tier | Daily Limit | Monthly Limit |
|---|---|---|
| `unauth` | — | 10 requests |
| `free` | 100 | 100 |
| `pro` | Unlimited | Unlimited |

---

## Database Collections

| Collection | Description |
|---|---|
| `logins` | User profiles (email, username, hashed password, profile image) |
| `api_keys` | User-generated API keys for programmatic access |
| `api_usage` | Daily/monthly usage tracking per user |
| `contact_messages` | Contact form submissions |

---

## Logging

All requests are logged via `StructuredLoggingMiddleware` with:
- Request method, path, duration
- LLM token counts (input/output)
- User identifier and auth type
- Error details on failure

Logs are written to `app/logs/app.log` and optionally streamed to Logfire.
