## tasks

- Enforced structured citations in RAG answers.
  - Updated prompts to require JSON-only output with `answer` and `citations` indices.
  - Added a one‑retry path if the model returns no citations.
  - Improved citation extraction to parse JSON first, then fall back to `[n]` markers.

- Fixed streaming to uphold mandatory citations.
  - Streaming now emits normal text chunks, then a final SSE `meta` event containing citations, topics, language, and disclaimer.
  - Frontend streaming client updated to parse SSE `event:` frames and attach metadata instead of returning empty citations.

- Hardened pgvector retrieval.
  - Query embeddings are now formatted as proper pgvector literals instead of Python list strings.

- Added embedding/ingestion script.
  - New `backend/scripts/generate_embeddings.py` reads `data/processed/**/*.json`, generates embeddings in batches, and seeds `knowledge_chunks`.

## files edited/created

- `backend/app/services/rag/prompts.py`
- `backend/app/services/rag/citation.py`
- `backend/app/services/rag/retriever.py`
- `backend/app/services/rag/pipeline.py`
- `backend/app/routers/chat.py`
- `frontend/src/services/chatService.ts`
- `backend/scripts/generate_embeddings.py`

---

## Session 3: Database Setup & Embedding Generation

### Fixed SQLAlchemy Model Issues
- Renamed `metadata` column to `source_metadata` in `KnowledgeSource` model
- Renamed `metadata` column to `chunk_metadata` in `KnowledgeChunk` model
- Updated `backend/sql/schema.sql` and `backend/app/models/knowledge.py`
- Fixed column references in `generate_embeddings.py`

### Docker Infrastructure
Configured PostgreSQL, Redis, and pgAdmin containers:

**Services:**
- PostgreSQL 16 + pgvector: `localhost:5432`
- Redis: `localhost:6379`
- pgAdmin: `http://localhost:5050`

**Credentials:**
- DB User: `ilmuai_admin`
- DB Password: `secret123`
- DB Name: `ilmuai`
- pgAdmin Email: `admin@admin.com`
- pgAdmin Password: `secret123`

**pgAdmin Connection:**
- Host: `ilmuai-postgres` (Docker service name)
- Port: `5432`
- Database: `ilmuai`

**Important:** Stopped Homebrew PostgreSQL (`brew services stop postgresql@14`) to free port 5432 for Docker container.

### Embedding Generation Results
Successfully generated embeddings for all processed data:
- **Total chunks:** 27,081
- **Hadith:** 18,724 chunks
- **Quran:** 8,351 chunks
- **Fiqh:** 6 chunks

**Command used:**
```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/generate_embeddings.py --batch-size 100
```

### Files Modified
- `backend/app/models/knowledge.py`
- `backend/sql/schema.sql`
- `backend/scripts/generate_embeddings.py`
- `backend/.env`
- `docker/docker-compose.yml`
- `backend/app/config.py` (removed lru_cache temporarily)
