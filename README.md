# My Teacher

An AI-powered learning platform split into two services:

- `my-t-backend-services` (FastAPI): authentication, conversations, document workflows, AI learning tools, and speech endpoints.
- `my-t-frontend-services` (React): web UI for chat, document upload, and education-focused tools.

## Project Structure

```text
my-teacher/
├── my-t-backend-services/   # Python FastAPI backend
└── my-t-frontend-services/  # React frontend
```

## What This Platform Does

The platform is built for learning workflows, not just generic chat. Current backend/frontend structure supports:

- chat and responder workflows
- conversation history
- document upload and document QA
- auth + refresh-token flow
- flashcards, study plans, key concepts, topic breakdowns, MCQ generation, and visuals
- speech-to-text and text-to-speech

## Prerequisites

### Backend

- Python 3.10+ (recommended 3.11/3.12)
- `pip`

### Frontend

- Node.js 18+
- npm

## Environment Setup

### 1) Backend environment

From `my-t-backend-services`:

1. Copy the example env file:
   - `cp .env.example .env.local`
2. Set environment selector:
   - `export AI_ENV=local`
3. Ensure your selected file exists:
   - backend loads `.env.<AI_ENV>` (for local: `.env.local`)

Important variables to fill:

- `OPENAI_API_KEY`
- `DEFAULT_MODEL`
- `MONGODB_URI`
- `PORT` (commonly `9500`)
- `API_PREFIX` (commonly `/api`)

### 2) Frontend environment

From `my-t-frontend-services`:

1. Copy the example env file:
   - `cp .env.example .env`
2. Verify frontend display and backend settings.

Important variables:

- `REACT_APP_BASE_BACKEND_URL=http://localhost:9500` (used in production-mode absolute URL paths)
- `REACT_APP_PAGE_TITLE` and other UI text variables

Note: in development, the app proxies API requests to backend via `proxy` in `package.json` (`http://127.0.0.1:9150`) and `apiRequest` uses `/api/v1`.

## Run Locally

## 1) Start backend

```bash
cd my-t-backend-services
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$(pwd)"
export AI_ENV=local
python app/main.py
```

By default, API base path is:

- `http://localhost:9500/api/v1`

## 2) Start frontend (new terminal)

```bash
cd my-t-frontend-services
npm install
npm start
```

Frontend starts on:

- `http://localhost:9100`

## Key API Areas (Backend)

The backend includes routes under `/api/v1` such as:

- `/health`
- `/auth`
- `/conversations`
- `/upload`
- `/document-qa`
- `/responder`
- `/flashcards`
- `/breakdowns`
- `/explanations`
- `/key-concepts`
- `/multiple-choice-questions`
- `/study-plan`
- `/visuals`
- `/speech`

## Frontend Scripts

From `my-t-frontend-services`:

- `npm start` - run dev server on port 9100
- `npm run build` - production build
- `npm run lint` - lint source
- `npm run check-all` - lint + build + dependency audit

## Troubleshooting

- 401/session expiry: frontend has automatic token refresh flow; verify backend `/auth/refresh` is working.
- CORS issues: confirm backend is running and frontend uses the expected host/port combination.
- Backend config errors: ensure `AI_ENV` matches an existing `.env.<AI_ENV>` file.
- API not reachable from frontend: verify frontend proxy target and backend `PORT`.

## Notes

- The backend and frontend are maintained as separate service folders inside this root.
- Keep secrets only in local env files (`.env.local`, `.env`) and never commit real credentials.
