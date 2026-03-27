# MyTeacher — Frontend

React-based frontend for the MyTeacher AI study companion. Provides a chat interface, learning tools, authentication, and user profile management.

---

## Tech Stack

| Layer | Library / Tool |
|---|---|
| Framework | React 18 + React Router v6 |
| UI | Material UI (MUI) v5 + Emotion |
| Styling | Tailwind CSS v3 |
| State | React Context API |
| HTTP | Custom `apiRequest` utility with JWT auto-refresh |
| Markdown | react-markdown + remark-gfm + remark-math + rehype-katex |
| Diagrams | ReactFlow |
| Data Fetching | TanStack React Query v5 |
| Build | React Scripts (Create React App) |

---

## Getting Started

### Prerequisites
- Node.js 18+
- Backend running at `http://localhost:9150`

### Install & Run

```bash
cd my-t-frontend-services
npm install
cp .env.example .env      # fill in values
npm start                 # http://localhost:9100
```

### Build for Production

```bash
npm run build
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
REACT_APP_BASE_BACKEND_URL=http://localhost:9150
REACT_APP_TITLE=MyTeacher
REACT_APP_PAGE_TITLE=MyTeacher - AI Study Companion
REACT_APP_DESCRIPTION=Your personal AI-powered study companion

HOST=0.0.0.0
DANGEROUSLY_DISABLE_HOST_CHECK=true   # required for ngrok / tunnels
```

---

## Project Structure

```
src/
├── pages/                  # Route-level pages
│   ├── IndexPage.js        # Landing page
│   ├── AuthPage.js         # Login / Register / Forgot password
│   ├── ChatPage.js         # Main chat interface
│   ├── ProfilePage.js      # User profile & settings
│   ├── ExplorePage.js      # Explore page
│   ├── ContactPage.js      # Contact form
│   ├── auth/               # Auth section sub-components
│   └── profile/            # Profile section sub-components
│
├── components/
│   ├── Layout/             # PageLayout, Header, Footer
│   ├── Chat/
│   │   ├── ChatInput.jsx         # Message input bar
│   │   ├── MessageBubble.jsx     # Renders individual messages
│   │   ├── LeftSidebar.jsx       # Conversation history
│   │   ├── RightSidebar.jsx      # Documents & learning tools
│   │   ├── DocumentsList.jsx     # Uploaded documents list
│   │   ├── TypingIndicator.jsx   # Animated typing dots
│   │   └── ToolCallingIndicator.jsx  # AI tool-use indicator
│   └── ProtectedRoute.js   # Auth-guarded route wrapper
│
├── external_pages/         # Standalone learning tool views
│   ├── Flashcard.jsx
│   ├── KeyConcepts.jsx
│   ├── MCQSet.jsx
│   ├── QAPairs.jsx
│   ├── StudyPlan.jsx
│   ├── TopicBreakdown.jsx
│   └── VisualFlowchart.jsx
│
├── contexts/
│   ├── AuthContext.js      # User auth state + JWT refresh
│   ├── SettingsContext.js  # Theme, model, streaming prefs
│   └── ApiKeyContext.js    # User API key management
│
├── services/
│   ├── auth/
│   │   ├── authService.js        # Login, register, profile, logout
│   │   └── apiKeyService.js      # API key CRUD
│   ├── chat/
│   │   ├── responderService.js   # AI responder API
│   │   └── conversationService.js
│   ├── fileUpload/
│   │   ├── documentService.js    # Upload & retrieve documents
│   │   └── fileValidation.js     # Client-side file checks
│   ├── learning/
│   │   └── learningService.js    # Flashcards, MCQs, study plans, etc.
│   └── speech/
│       └── speechService.js      # TTS / STT
│
├── utils/
│   ├── apiRequest.js             # Fetch wrapper + TokenManager (JWT)
│   └── toolHandlers/
│       ├── streamingHandlers.js  # Handles SSE / streaming responses
│       └── traditionalHandlers.js
│
└── constants/
    └── chatConstants.js          # Welcome messages, tool list
```

---

## Pages & Routing

| Route | Page | Auth Required |
|---|---|---|
| `/` | IndexPage | No |
| `/login` | LoginPage | No |
| `/auth` | AuthPage | No |
| `/chat` | ChatPage | No (anonymous allowed) |
| `/chat/:conversationId` | ChatPage | No |
| `/profile` | ProfilePage | Yes |
| `/explore` | ExplorePage | Yes |
| `/contact` | ContactPage | No |

---

## Authentication

- JWT tokens stored in `localStorage` (`accessToken`, `refreshToken`)
- `TokenManager` in `apiRequest.js` handles:
  - Proactive refresh when token expires within 10 minutes
  - Reactive refresh on `401` responses
  - Auto-logout when refresh fails
- `AuthContext` runs a background check every 5 minutes

---

## Learning Tools

Accessible from the right sidebar in the chat:

| Tool | Description |
|---|---|
| Flashcards | Generate flashcard sets from content |
| Key Concepts | Extract and highlight key concepts |
| Topic Breakdown | Visual topic decomposition |
| MCQ | Multiple-choice question generator |
| Q&A Pairs | Generate question-answer pairs |
| Study Plan | Personalized study schedule |
| Visual Flowchart | Auto-generated diagrams |

---

## Settings

Configurable per-user via `SettingsContext` (persisted to `localStorage`):

- **Theme** — Light / Dark
- **Model** — LLM model selection
- **Response Mode** — Streaming vs. Traditional
- **Right Sidebar** — Toggle visibility
