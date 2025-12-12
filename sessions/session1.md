# Session 1: Project Foundation

**Date:** December 11, 2024
**Duration:** ~2 hours
**Focus:** Initial project setup and core implementation

---

## Summary

Built the complete foundation of IlmuAI from scratch - an AI-powered Islamic knowledge platform for Malaysian Muslims. Created a full-stack application with FastAPI backend, React frontend, and infrastructure setup.

---

## What Was Accomplished

### 1. Project Planning
- Reviewed PRD document from `/Users/faiqhilman/Documents/Obsidian Vault/AI Docs/IlmuAI/PRD.md`
- Created implementation plan at `/Users/faiqhilman/.claude/plans/structured-hugging-dove.md`
- Identified key decisions:
  - **Stack:** FastAPI + React + PostgreSQL/pgvector
  - **LLM:** Both OpenAI and Anthropic (switchable)
  - **Deployment:** Local development first
  - **Data:** Need to source Quran, Hadith, Fiqh texts

### 2. Backend Implementation (FastAPI)

**Core Structure:**
- `backend/app/main.py` - FastAPI app with CORS, lifespan events
- `backend/app/config.py` - Pydantic settings with all configuration
- `backend/app/dependencies.py` - Auth dependencies (CurrentUser, Database)

**Database Layer:**
- `backend/sql/schema.sql` - Full PostgreSQL schema with pgvector
- SQLAlchemy models: User, Conversation, Message, Bookmark, KnowledgeChunk

**API Routers:**
- `/api/auth` - Register, Login, Get current user
- `/api/chat` - Send message, streaming, suggestions
- `/api/conversations` - CRUD for conversations
- `/api/bookmarks` - CRUD for bookmarks

**Services:**
- **LLM Abstraction Layer:**
  - `services/llm/base.py` - Abstract base class
  - `services/llm/openai_client.py` - OpenAI implementation
  - `services/llm/anthropic_client.py` - Claude implementation
  - `services/llm/factory.py` - Provider switching factory

- **RAG Pipeline:**
  - `services/rag/pipeline.py` - Main orchestration
  - `services/rag/retriever.py` - pgvector semantic search
  - `services/rag/citation.py` - Citation extraction & formatting
  - `services/rag/prompts.py` - Islamic Q&A prompts (BM/EN)

- **Safety Layer:**
  - `services/safety/classifier.py` - Topic classification (aqidah, fiqh, etc.)
  - `services/safety/disclaimers.py` - Bilingual disclaimers

### 3. Frontend Implementation (React + TypeScript)

**Setup:**
- Vite + React + TypeScript
- Tailwind CSS with custom Islamic-themed colors
- i18n with react-i18next (BM/EN)
- Zustand for state management
- TanStack Query for API calls

**Pages:**
- `ChatPage.tsx` - Main chat interface
- `LoginPage.tsx` - User login
- `RegisterPage.tsx` - User registration

**Components:**
- **Chat:** ChatContainer, MessageList, UserMessage, AssistantMessage, ChatInput, SuggestedQuestions, LoadingMessage
- **Citation:** CitationList, CitationCard (with expandable Quran/Hadith/Fiqh views)
- **Common:** Header, Sidebar

**Services & Stores:**
- `services/api.ts` - Axios instance with auth interceptor
- `services/chatService.ts` - Chat API calls
- `services/authService.ts` - Auth API calls
- `stores/authStore.ts` - Auth state (persisted)
- `stores/chatStore.ts` - Chat state

### 4. Infrastructure

**Docker:**
- `docker/docker-compose.yml` - PostgreSQL (pgvector) + Redis

**Data Pipeline:**
- `data/scripts/download_quran.py` - Script to download Quran from Tanzil.net

**Documentation:**
- `README.md` - Project overview and setup instructions
- `CLAUDE.md` - Claude Code instructions
- `.gitignore` - Comprehensive ignore file

---

## Files Created (68 total)

### Backend (35 files)
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   └── bookmarks.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── openai_client.py
│   │   │   ├── anthropic_client.py
│   │   │   └── factory.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py
│   │   │   ├── retriever.py
│   │   │   ├── citation.py
│   │   │   └── prompts.py
│   │   └── safety/
│   │       ├── __init__.py
│   │       ├── classifier.py
│   │       └── disclaimers.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── bookmark.py
│   │   └── knowledge.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── citation.py
│   │   ├── conversation.py
│   │   └── bookmark.py
│   └── core/
│       ├── __init__.py
│       ├── database.py
│       ├── redis.py
│       └── exceptions.py
├── sql/
│   └── schema.sql
├── requirements.txt
└── .env.example
```

### Frontend (25 files)
```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── i18n/
│   │   └── config.ts
│   ├── types/
│   │   └── index.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── chatService.ts
│   │   └── authService.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   └── chatStore.ts
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   └── components/
│       ├── common/
│       │   ├── Header.tsx
│       │   └── Sidebar.tsx
│       ├── chat/
│       │   ├── ChatContainer.tsx
│       │   ├── MessageList.tsx
│       │   ├── UserMessage.tsx
│       │   ├── AssistantMessage.tsx
│       │   ├── ChatInput.tsx
│       │   ├── LoadingMessage.tsx
│       │   └── SuggestedQuestions.tsx
│       └── citation/
│           ├── CitationList.tsx
│           └── CitationCard.tsx
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── .env.example
```

### Other (8 files)
```
ilmuai/
├── .gitignore
├── README.md
├── CLAUDE.md
├── docker/
│   └── docker-compose.yml
└── data/
    ├── raw/.gitkeep
    ├── processed/.gitkeep
    └── scripts/
        └── download_quran.py
```

---

## Key Design Decisions

1. **Monorepo Structure** - Single repo for backend, frontend, and data pipeline
2. **LLM Abstraction** - Factory pattern to switch between OpenAI and Anthropic
3. **Citation Types** - Separate schemas for Quran, Hadith, Fiqh, Fatwa citations
4. **Safety First** - Topic classification with sensitivity levels and mandatory disclaimers
5. **Malaysian Context** - Shafi'i madhab focus, BM as primary language, JAKIM alignment
6. **No Alembic** - Raw SQL for MVP simplicity, can add migrations later

---

## Data Sources Identified

| Source | Description | URL |
|--------|-------------|-----|
| **Quran** | Arabic + BM translation (Basmeih) | tanzil.net/download |
| **Hadith** | Six major collections with grading | sunnah.com |
| **Shafi'i Fiqh** | Al-Fiqh Al-Manhaji (JAKIM) | archive.org/details/Fiqhmanhaji1 |
| **Fatwa** | Malaysian fatwas | e-smaf.islam.gov.my |

---

## What's NOT Done Yet

1. **Data Pipeline** - Need to download, process, and embed Islamic texts
2. **Database Seeding** - No knowledge chunks in database yet
3. **Testing** - No unit or integration tests
4. **Frontend Polish** - Bookmarks page, Settings page not implemented
5. **Deployment** - Only local development setup

---

## Commands to Run

```bash
# Start infrastructure
cd /Users/faiqhilman/Projects/ilmuai/docker
docker-compose up -d

# Backend
cd ../backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API keys
uvicorn app.main:app --reload

# Frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

---

## Notes

- The RAG pipeline is complete but won't work until we have embeddings in the database
- Frontend can run and show UI, but chat won't work without backend + data
- All schemas and types are defined, making it easy to extend

---

*Session documented by Claude Code*
