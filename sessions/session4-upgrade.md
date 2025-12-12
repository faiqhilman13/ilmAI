## tasks

- Upgraded retrieval stage to a hybrid, multi‑query pipeline.
  - Added **hybrid dense + sparse search**: pgvector cosine similarity + Postgres full‑text (BM25‑style) search.
  - Fused dense/sparse (and multi‑query) results with **Reciprocal Rank Fusion (RRF)**.
  - Added **LLM search planner** to generate up to `rag_num_rewrites` query rewrites (English/Malay/Arabic/transliteration) and optional structured filters.
  - Added **regex heuristics** for explicit references (e.g., `2:255`, “Hadith #20”, “Bukhari”) to short‑circuit planning when obvious.
  - Added **explicit Quran range handling**:
    - Normalizes Unicode dashes (e.g., `88:14‑16`) so ranges parse correctly.
    - Forces all ayahs in a requested range into context and preserves them through reranking.
  - Implemented **source priors + balanced top‑k**:
    - Heuristic weights to nudge Quran/Hadith/Fiqh/Fatwa based on intent cues.
    - Ensures `rag_per_source_k` per source before filling remaining slots **only for Quran‑cue queries**.
  - Added **Quran context window expansion** (conditional on Quran cues): when a single‑ayah Quran chunk is retrieved, automatically include neighboring ayahs (±`rag_quran_context_window`) for richer context.

- Added a two‑stage reranking step after retrieval.
  - **Cross‑encoder reranker** (default `BAAI/bge-reranker-base`) reorders retrieved chunks by pairwise relevance.
  - **LLM‑judge reranker** reorders the top candidates again using GPT for final relevance ordering.
  - Final context uses the top `rag_rerank_top_k` reranked chunks.

- Improved RAG debugging logs.
  - Added colored boxed log sections for: user query, topic classification, retrieval plan/results, rerank stages, final context order, citations used, raw LLM response, and final answer.
  - Makes it easy to visually trace each pipeline stage in backend logs.

- Fixed Quran citation metadata mapping.
  - Uses `surah_name_ms/en` when `surah_name` is missing.
  - Uses `ayah_number` for single‑ayah chunks so titles/snippets show correct ayah numbers.

- Added configuration knobs for all retrieval upgrades:
  - `rag_use_hybrid`, `rag_dense_candidates`, `rag_sparse_candidates`, `rag_rrf_k`
  - `rag_multi_query`, `rag_num_rewrites`
  - `rag_self_filtering`
  - `rag_per_source_k`, `rag_use_source_priors`
  - `rag_quran_context_window`
  - `rag_use_cross_encoder_rerank`, `rag_cross_encoder_model`
  - `rag_use_llm_judge_rerank`, `rag_llm_judge_candidates`

- Added database support for sparse search performance:
  - New GIN full‑text index on `knowledge_chunks.text_content`.

## files edited/created

- `backend/app/services/rag/retriever.py`
- `backend/app/services/rag/pipeline.py`
- `backend/app/services/rag/citation.py`
- `backend/app/services/rag/reranker.py`
- `backend/app/services/rag/logging_utils.py`
- `backend/app/config.py`
- `backend/sql/schema.sql`
- `backend/requirements.txt`

## notes / next steps

- Apply the new FTS index to your running DB if needed:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_text_fts
  ON knowledge_chunks
  USING GIN (to_tsvector('simple', text_content));
  ```
- If latency/cost is high, disable planning or reduce rewrites:
  - set `rag_multi_query=false` and/or `rag_self_filtering=false`.
- Next tuning targets once you have a small eval set:
  - `rag_score_threshold`, `rag_rrf_k`, `rag_per_source_k`, and source priors.
