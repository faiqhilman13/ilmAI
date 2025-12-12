# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IlmuAI is an AI-powered Islamic knowledge platform for Malaysian Muslims with RAG-based Q&A, mandatory citations, and multi-language support (Bahasa Malaysia primary, English secondary).

**Key Constraint:** All responses MUST include citations from authentic sources. The system refuses to generate unsourced Islamic knowledge.

## Architecture Overview

### Core Pipeline: Advanced RAG + Safety + Citations

**Full Pipeline Flow:**
1. **User Question** (EN/MS) →
2. **Topic Classification** (safety check for sensitive topics) →
3. **LLM Query Planner** (rewrites + explicit reference detection) →
4. **Hybrid Retrieval** (dense + sparse search with RRF fusion) →
5. **Context Expansion** (Quran neighbor ayahs + source balancing) →
6. **Two-Stage Reranking** (cross-encoder + LLM judge) →
7. **LLM Generation** (structured JSON output) →
8. **Citation Extraction** (validate + map to chunks) →
9. **Answer Assembly** (format + add disclaimer) →
10. **Response** (citations + disclaimer + topics)

### Service Layer Structure

**LLM Abstraction (`backend/app/services/llm/`)**
- `base.py`: Abstract interface (chat, embeddings, streaming)
- `factory.py`: Provider switching (OpenAI ↔ Anthropic)
- `openai_client.py` / `anthropic_client.py`: Implementations
- Note: Anthropic doesn't have embedding API, uses OpenAI for embeddings

**RAG Pipeline (`backend/app/services/rag/`)**
- `retriever.py`: Hybrid retrieval (dense pgvector + sparse FTS BM25) with RRF fusion, multi-query expansion, query planning
- `pipeline.py`: Main orchestration (plan → retrieve → rerank → generate → extract citations)
- `reranker.py`: Cross-encoder (BAAI/bge-reranker-base) + LLM judge for two-stage reranking
- `citation.py`: Citation metadata extraction + validation from LLM responses
- `logging_utils.py`: Colored boxed debug logging for each pipeline stage
- `prompts.py`: System/user prompts (bilingual, context-aware, structured JSON)

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

### Retrieval Pipeline (Session 4 Upgrade)
**Hybrid Dense + Sparse Search:**
- **Dense Search**: pgvector cosine similarity (OpenAI text-embedding-3-small, 1536 dims)
- **Sparse Search**: PostgreSQL full-text search (BM25-style) with GIN index
- **Fusion**: Reciprocal Rank Fusion (RRF) to combine both result sets
- **Index**: IVFFlat (100 lists) on embeddings, GIN on text_content

**Query Planning:**
- LLM generates up to `rag_num_rewrites` query rewrites (EN/MS/AR/transliteration variants)
- Regex heuristics detect explicit references (e.g., `2:255`, "Hadith #20", "Bukhari")
- Structured filter extraction for source/madhab/topic constraints
- Multi-query expansion improves recall for ambiguous questions

**Context Expansion:**
- Quran neighbor ayahs: When single-ayah chunk retrieved, includes ±`rag_quran_context_window` ayahs
- Source balancing: `rag_per_source_k` per source to ensure diverse results (configurable per query intent)
- Explicit range handling: Normalizes Unicode dashes (`88:14‑16` → `88:14-16`) for correct range parsing

**Two-Stage Reranking:**
- Stage 1: Cross-encoder (BAAI/bge-reranker-base) for pairwise relevance scoring
- Stage 2: LLM judge (GPT) for final relevance ordering on top `rag_llm_judge_candidates`
- Final context uses top `rag_rerank_top_k` reranked chunks

### pgvector Configuration
- Dimension: 1536 (OpenAI text-embedding-3-small)
- Index: IVFFlat (100 lists) for performance
- Search: Cosine similarity
- **Important**: Index is created in `backend/sql/schema.sql` - must re-create if dimension changes
- **FTS Index**: GIN index on `text_content` for sparse search (created post-Session 4)

### Citation Extraction
The RAG pipeline uses structured JSON output from LLM:
- LLM returns JSON with `answer`, `citations: [{type, source_type, references...}]` fields
- Citation matcher validates references against available chunks
- Automatically fallbacks to unstructured parsing if JSON parsing fails
- Supports QuranCitation, HadithCitation, FiqhCitation, FatwaCitation types

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

1. **Backend Configuration**: `backend/app/config.py` (all RAG settings: `rag_use_hybrid`, `rag_num_rewrites`, `rag_per_source_k`, etc.)
2. **Main FastAPI App**: `backend/app/main.py` (lifespan, dependency injection, logging setup)
3. **Chat Router**: `backend/app/routers/chat.py` (orchestrates RAG pipeline, streaming)
4. **RAG Retriever**: `backend/app/services/rag/retriever.py` (hybrid search, multi-query, planning)
5. **RAG Reranker**: `backend/app/services/rag/reranker.py` (cross-encoder + LLM judge)
6. **RAG Pipeline**: `backend/app/services/rag/pipeline.py` (orchestrates entire flow with colored logging)
7. **Database Schema**: `backend/sql/schema.sql` (pgvector + FTS index setup)

## Testing & Debugging

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Try endpoints directly in Swagger

### Debug Tips
- **Colored RAG Logs**: Each pipeline stage (query planning, retrieval, reranking, generation, citations) is in colored boxes
- Check `backend/app/services/rag/logging_utils.py` for debug section customization
- Query planner logs: Query rewrites, detected references, source priorities
- Retriever logs: Dense + sparse results, RRF scores, context expansion
- Reranker logs: Cross-encoder + LLM judge ordering
- Citation extraction logs: Matched citations, validation results
- Frontend chat state: Check `chatStore.ts` for message flow

## Important Architectural Constraints

1. **No Fatwa Generation**: Safety layer prevents issuing religious rulings for sensitive topics
2. **Citation Requirement**: Every factual claim in RAG response must have a source reference
3. **Bilingual by Default**: All prompts, disclaimers, and UI should support both BM and EN
4. **Shafi'i Madhab Focus**: When madhab-specific, default to Shafi'i (Malaysian Islamic standard)
5. **LLM Agnostic**: Backend designed to switch between OpenAI/Anthropic without code changes (config only)

## RAG Configuration Tuning Knobs

All these settings are in `backend/app/config.py` and can be tweaked for different performance/quality tradeoffs:

**Retrieval Settings:**
- `rag_use_hybrid`: Enable/disable hybrid dense+sparse (default: True)
- `rag_dense_candidates`: Top-K from dense search before RRF (default: 50)
- `rag_sparse_candidates`: Top-K from sparse search before RRF (default: 50)
- `rag_rrf_k`: RRF constant for fusion (default: 60)
- `rag_score_threshold`: Minimum similarity for chunk inclusion (default: 0.3, lower = more permissive)

**Query Expansion:**
- `rag_multi_query`: Enable/disable query rewrites (default: True)
- `rag_num_rewrites`: Max number of rewrites per language (default: 3)
- `rag_self_filtering`: Filter out low-confidence rewrites (default: True)

**Source Balancing:**
- `rag_per_source_k`: Chunks per source for balanced retrieval (default: 5, Quran-cue only)
- `rag_use_source_priors`: Enable source weighting based on query intent (default: True)

**Context Expansion:**
- `rag_quran_context_window`: Ayahs to include left/right of single-ayah chunks (default: 3)

**Reranking:**
- `rag_use_cross_encoder_rerank`: Enable Stage 1 reranking (default: True)
- `rag_cross_encoder_model`: Model for Stage 1 (default: "BAAI/bge-reranker-base")
- `rag_use_llm_judge_rerank`: Enable Stage 2 LLM reranking (default: True)
- `rag_llm_judge_candidates`: Top-K chunks for LLM judge (default: 10)
- `rag_rerank_top_k`: Final context size after reranking (default: 8)

## Session History

- **Session 3** (Dec 12): Fixed XML parsing (CRLF handling), Quran translation embedding, hadith/fiqh data
- **Session 4** (Dec 12): Advanced RAG upgrade - hybrid search, query planning, reranking, logging
- See `sessions/` directory for detailed notes per session
