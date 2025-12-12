# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IlmuAI is an AI-powered Islamic knowledge platform for Malaysian Muslims with RAG-based Q&A, mandatory citations, and multi-language support (Bahasa Malaysia primary, English secondary).

**Key Constraint:** All responses MUST include citations from authentic sources. The system refuses to generate unsourced Islamic knowledge.

## Architecture Overview

### Core Pipeline: RAG + Safety + Citations

1. **User Question** → 2. **Topic Classification** (safety check) → 3. **Vector Search** (pgvector) → 4. **LLM Generation** → 5. **Citation Extraction** → 6. **Response with Disclaimer**

### Service Layer Structure

**LLM Abstraction (`backend/app/services/llm/`)**
- `base.py`: Abstract interface (chat, embeddings, streaming)
- `factory.py`: Provider switching (OpenAI ↔ Anthropic)
- `openai_client.py` / `anthropic_client.py`: Implementations
- Note: Anthropic doesn't have embedding API, uses OpenAI for embeddings

**RAG Pipeline (`backend/app/services/rag/`)**
- `retriever.py`: pgvector semantic search + metadata filtering
- `pipeline.py`: Main orchestration (retrieve → prompt → extract citations)
- `citation.py`: Citation metadata extraction from LLM responses
- `prompts.py`: System/user prompts (bilingual, context-aware)

**Safety Layer (`backend/app/services/safety/`)**
- `classifier.py`: Topic classification + sensitivity detection (aqidah, munakahat, contemporary issues)
- `disclaimers.py`: Bilingual disclaimers for sensitive topics
- Policy: Never issue fatwas, always refer to scholars for sensitive issues

### Data Pipeline

**Download Scripts** (`data/scripts/`):
- `download_quran.py`: Tanzil.net XML (Arabic Uthmani + BM Basmeih + EN Sahih)
- `download_hadith.py`: GitHub JSON datasets (6 collections) + sunnah.com API optional
- `download_fiqh.py`: Internet Archive PDFs + sample JSON with Al-Fiqh Al-Manhaji Shafi'i rulings

**Processing Scripts** (`data/scripts/`):
- `process_quran.py`: XML → chunks (individual ayahs + grouped 3-ayah chunks for context)
- `process_hadith.py`: JSON → normalized chunks (grading normalization: sahih/hasan/daif/maudu)
- `process_fiqh.py`: JSON + optional PDF → topic-classified chunks (taharah, solat, puasa, etc.)

Outputs go to `data/processed/{quran,hadith,fiqh}/` as JSON files ready for embedding.

### Frontend Architecture

**State Management**: Zustand stores (`stores/`)
- `authStore.ts`: JWT tokens, user session (persisted to localStorage)
- `chatStore.ts`: Current conversation, messages, UI state

**API Integration**: TanStack Query + custom axios with auth interceptor (`services/`)
- `chatService.ts`: SSE streaming for real-time responses
- `authService.ts`: Login/register endpoints

**Key Components**:
- `ChatContainer.tsx`: Main orchestration (fetch history, handle streaming)
- `AssistantMessage.tsx`: Renders response + expandable `CitationCard` components
- `CitationCard.tsx`: Displays citation metadata (Quran surah/ayah, Hadith collection/grading, Fiqh topic/madhab)

## Common Development Tasks

### Add a New API Endpoint

1. Create schema in `backend/app/schemas/` (Pydantic models for request/response)
2. Create router file in `backend/app/routers/` (FastAPI router)
3. Add service logic in `backend/app/services/` if needed
4. Import and include router in `backend/app/main.py` (lifespan setup)
5. Document in API docstring

Example: `/api/bookmarks` endpoint (model, schema, router all follow this pattern)

### Modify Citation Behavior

- **Citation Format**: See `backend/app/schemas/citation.py` (QuranCitation, HadithCitation, FiqhCitation, FatwaCitation)
- **Citation Extraction**: `backend/app/services/rag/citation.py` (parses LLM output for source references)
- **Display**: `frontend/src/components/citation/CitationCard.tsx`

### Add Safety Rules or Disclaimers

1. Update topic keywords in `backend/app/services/safety/classifier.py` (TOPIC_KEYWORDS)
2. Add/modify sensitivity rules in `check_sensitivity()` method
3. Add disclaimer text in `backend/app/services/safety/disclaimers.py` (bilingual)

### Process New Islamic Knowledge Source

1. Create download script in `data/scripts/download_*.py`
2. Create processing script in `data/scripts/process_*.py`
3. Output standardized JSON: `[{"source_type": "...", "text_content": "...", "metadata": {...}}]`
4. Create `backend/scripts/generate_embeddings.py` to embed and seed `knowledge_chunks` table

## Critical Implementation Details

### pgvector Configuration
- Dimension: 1536 (OpenAI text-embedding-3-small)
- Index: IVFFlat (100 lists) for performance
- Search: Cosine similarity
- **Important**: Index is created in `backend/sql/schema.sql` - must re-create if dimension changes

### Citation Extraction
The RAG pipeline expects LLM to include source references in specific format:
- Format is NOT enforced currently - relies on prompt engineering
- Consider implementing structured output parsing (JSON in response) for reliability

### Language Support
- Response language set per conversation (BM default for Malaysia)
- Frontend i18n via `react-i18next` with `frontend/src/i18n/config.ts`
- Prompts are bilingual in `prompts.py` - uses `language` parameter to select

### Database Models
- `knowledge_chunks`: Stores all processed Islamic sources with embeddings
- `conversations` + `messages`: Store user interactions (supports history)
- `users`: Basic auth (email/password with JWT)
- Triggers auto-update `updated_at` timestamps

## Running Commands

### Backend Setup & Run
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Configure API keys
uvicorn app.main:app --reload # Runs on :8000
```

### Frontend Setup & Run
```bash
cd frontend
npm install
cp .env.example .env
npm run dev                    # Runs on :5173
```

### Data Pipeline
```bash
cd /Users/faiqhilman/Projects/ilmuai
python data/scripts/download_quran.py   # Downloads to data/raw/quran/
python data/scripts/download_hadith.py  # Downloads to data/raw/hadith/
python data/scripts/download_fiqh.py    # Downloads to data/raw/fiqh/
python data/scripts/process_quran.py    # Outputs to data/processed/quran/
python data/scripts/process_hadith.py   # Outputs to data/processed/hadith/
python data/scripts/process_fiqh.py     # Outputs to data/processed/fiqh/
# Next: Create backend/scripts/generate_embeddings.py to seed database
```

### Infrastructure
```bash
cd docker
docker-compose up -d   # PostgreSQL (pgvector) + Redis
docker-compose down    # Stop services
```

## Key Files to Understand First

1. **Backend Configuration**: `backend/app/config.py` (all settings, LLM provider selection)
2. **Main FastAPI App**: `backend/app/main.py` (lifespan, dependency injection)
3. **Chat Router**: `backend/app/routers/chat.py` (orchestrates RAG pipeline)
4. **RAG Pipeline**: `backend/app/services/rag/pipeline.py` (core logic)
5. **Database Schema**: `backend/sql/schema.sql` (pgvector setup, table structure)

## Testing & Debugging

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Try endpoints directly in Swagger

### Debug Tips
- Enable logging: Check `backend/app/main.py` for logger setup
- RAG pipeline logs topic classification and retrieval in `IslamicRAGPipeline.answer()`
- Frontend chat state: Check `chatStore.ts` for message flow

## Important Architectural Constraints

1. **No Fatwa Generation**: Safety layer prevents issuing religious rulings for sensitive topics
2. **Citation Requirement**: Every factual claim in RAG response must have a source reference
3. **Bilingual by Default**: All prompts, disclaimers, and UI should support both BM and EN
4. **Shafi'i Madhab Focus**: When madhab-specific, default to Shafi'i (Malaysian Islamic standard)
5. **LLM Agnostic**: Backend designed to switch between OpenAI/Anthropic without code changes (config only)

## Next Major Work

- **Session 3**: Embedding generation and database seeding
- **Session 4**: End-to-end testing
- **Session 5**: Error handling, rate limiting, caching
- See `sessions/PLAN.md` for detailed roadmap
