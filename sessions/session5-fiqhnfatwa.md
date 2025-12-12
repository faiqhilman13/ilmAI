## tasks

- Added large‑scale fiqh + fatwa ingestion.
  - Extended fiqh processor to ingest the ADH/OpenITI corpus (`data/raw/fiqh/adh_fiqh_corpus/txt/`).
  - Added Arabic‑aware topic keywords (BM/EN/AR) for better categorisation.
  - Cleaned OpenITI markup and chunked with sliding window (`chunk_size=1200`, `overlap=200`).
  - Generated `data/processed/fiqh/fiqh_chunks.json` (~229k chunks, ~1GB).
  - Added MuftiWP fatwa crawler (Joomla site) for “Irsyad Hukum” categories.
  - Downloaded 1301 MuftiWP posts → `data/raw/fatwa/muftiwp_posts.json`.
  - Processed to ~9956 fatwa chunks → `data/processed/fatwa/fatwa_chunks.json`.

- Seeded fatwa embeddings into Postgres.
  - Inserted 9956 fatwa chunks with OpenAI embeddings.

- Attempted to seed full ADH fiqh embeddings but hit OpenAI quota.
  - Existing fiqh in DB remains partial.

- Improved embedding seeder for incremental runs.
  - Only seeds files ending with `*_chunks.json` (skips summaries).
  - Added `--max-items` to limit items per file for incremental/semi‑manual seeding.

- Updated RAG prompts for Arabic‑only fiqh chunks.
  - Context formatting avoids fake “Translation:” labels when `text_translation` is empty.
  - System prompt tells the LLM to translate Arabic evidence into the response language.

## files edited/created

- `data/scripts/process_fiqh.py`
- `data/scripts/download_fatwa.py`
- `data/scripts/process_fatwa.py`
- `backend/scripts/generate_embeddings.py`
- `backend/app/services/rag/prompts.py`
- `CLAUDE.md`

## runs / outputs

- `python3 data/scripts/process_fiqh.py`
  - Output: 229,477 fiqh chunks in `data/processed/fiqh/fiqh_chunks.json`.

- `python3 data/scripts/download_fatwa.py`
  - Output: 1301 raw posts in `data/raw/fatwa/muftiwp_posts.json`.

- `python3 data/scripts/process_fatwa.py`
  - Output: 9,956 fatwa chunks in `data/processed/fatwa/fatwa_chunks.json`.

- `PYTHONPATH=backend backend/.venv/bin/python backend/scripts/generate_embeddings.py --path data/processed/fatwa`
  - Inserted 9,956 fatwa embeddings into DB.

- Current DB counts (Dec 12):
  - `hadith`: 18,724
  - `quran`: 8,351
  - `fatwa`: 9,956
  - `fiqh`: 3,913 (≈3,887 tagged `ADH Fiqh Corpus`)

## remaining / next steps

### Embed remaining fiqh corpus

- Processed fiqh chunks available: **229,477 total**.
- Already embedded in DB: **3,913 fiqh**.
- Remaining to embed: **~225k chunks** (almost the entire ADH corpus).

### How to embed safely on your bigger PC

Important limitation: the seeder does **not** yet support offset/dedupe.  
If you rerun with a higher `--max-items`, it will re‑insert earlier items again.

Recommended approach:

1. Ensure OpenAI embedding quota/billing is sufficient.
2. (Optional but cleanest) wipe current fiqh rows first so you seed once from scratch:
   ```sql
   DELETE FROM knowledge_chunks WHERE source_type='fiqh';
   ```
3. Seed the full fiqh file in one go:
   ```bash
   cd backend
   PYTHONPATH=$PWD .venv/bin/python scripts/generate_embeddings.py \
     --path data/processed/fiqh \
     --batch-size 50
   ```
4. If quota forces multi‑run, **shard the file once** and seed each shard exactly once:
   - Split `fiqh_chunks.json` into smaller files under `data/processed/fiqh_shards/`, each named like `fiqh_shards_01_chunks.json`, etc.
   - Then run:
     ```bash
     PYTHONPATH=$PWD .venv/bin/python scripts/generate_embeddings.py \
       --path data/processed/fiqh_shards \
       --batch-size 50
     ```

### Optional future improvements

- Add `--offset` / resumable dedupe to `generate_embeddings.py`.
- Translate only retrieved Arabic fiqh snippets at answer‑time to improve citation cards.
