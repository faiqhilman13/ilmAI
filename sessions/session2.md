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
