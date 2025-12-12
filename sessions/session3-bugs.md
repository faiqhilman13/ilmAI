# Session 3 - Bugs Found & Resolved

## ✅ RESOLVED: Issue 1 - Database Connection Error
**Error:** `init_db()` failed with "Not an executable object: 'SELECT 1'"
**Root Cause:** SQLAlchemy async requires `text()` wrapper for raw SQL strings
**Fix Applied:** Added `from sqlalchemy import text` and wrapped query as `text("SELECT 1")`
**File:** `backend/app/core/database.py`
**Status:** ✅ FIXED - Database now connects successfully

---

## ✅ RESOLVED: Issue 2 - Hadith Chunks Missing Text Content
**Problem:** All 18,724 hadith chunks had no actual narration text, only metadata (ID + grading)
**Root Cause:** Processing script was looking for keys `hadithEnglish`, `english`, `text_en` but raw data uses `English_Text` and `Arabic_Text` (sunnah.com format)
**Fix Applied:**
- Updated `data/scripts/process_hadith.py` to check for `English_Text` and `Arabic_Text` keys
- Re-processed all 18,724 hadiths with full narration text
- Deleted old embeddings and regenerated with proper content
**Files:** `data/scripts/process_hadith.py`, database re-seeded
**Status:** ✅ FIXED - Hadiths now retrieve correctly with full text

---

## ✅ RESOLVED: Issue 3 - Limited Fiqh Data (6 → 13 Rulings)
**Previous:** Only 6 basic Fiqh chunks, Arabic-only, insufficient coverage
**Enhancement Applied:**
- Created `data/scripts/download_fiqh_v2.py` with 13 comprehensive bilingual Shafi'i rulings
- Topics now cover 9 categories: Taharah (2), Solat (3), Puasa (2), Zakat (1), Haji (1), Munakahat (1), Makanan (1), Muamalat (1), Jenayah (1)
- All rulings include both Bahasa Melayu and English text
- Re-processed and re-embedded fiqh data
**Files:** `data/scripts/download_fiqh_v2.py`, `data/raw/fiqh/enhanced_fiqh.json`
**Status:** ✅ IMPROVED - Better Fiqh coverage with bilingual content

---

## ✅ RESOLVED: Issue 4 - Citation Field Name Mismatch
**Problem:** Frontend showing empty citation cards - JSON using snake_case but TypeScript expecting camelCase
**Backend Response:** `{"source_type": "hadith", "hadith_number": "20", ...}`
**Frontend Expects:** `{"sourceType": "hadith", "hadithNumber": "20", ...}`
**Fix Applied:**
- Added `to_camel()` function to convert snake_case to camelCase
- Configured `BaseCitation` Pydantic model with `alias_generator=to_camel`
- Updated `ChatResponse` router with `response_model_by_alias=True`
- Updated citation serialization to use `model_dump(by_alias=True)`
**Files:** `backend/app/schemas/citation.py`, `backend/app/routers/chat.py`, `backend/app/schemas/chat.py`
**Status:** ✅ FIXED - Citations now display correctly in UI

---

## ✅ IMPROVED: Issue 5 - Insufficient Debug Logging
**Enhancement:** Added comprehensive debug logging to RAG pipeline
**What's logged:**
- Top 3 retrieved chunks with similarity scores and text previews
- Raw SQL query row counts
- LLM response preview (first 200 chars)
- Citation extraction count
- Final answer preview
**Files:** `backend/app/services/rag/pipeline.py`, `backend/app/services/rag/retriever.py`, `backend/app/main.py`
**Status:** ✅ IMPROVED - Much better visibility into retrieval quality

---

---

## Summary of Session 3 Achievements

### Data Quality Improvements
- **Hadith Data**: Re-processed 18,724 hadiths with full narration text (previously empty)
- **Fiqh Data**: Expanded from 6 to 13 comprehensive bilingual Shafi'i rulings
- **Total Embeddings**: 27,088 chunks (Quran: 8,351, Hadith: 18,724, Fiqh: 13)

### Bug Fixes
1. Database connection error (SQLAlchemy async `text()` wrapper)
2. Hadith text extraction (field name mapping)
3. Citation serialization (snake_case → camelCase)

### Infrastructure Improvements
- Comprehensive debug logging for RAG pipeline
- Better visibility into chunk retrieval and similarity scores
- Proper API response serialization with Pydantic aliases

### Files Modified
**Backend:**
- `app/core/database.py` - Fixed init_db()
- `app/services/rag/pipeline.py` - Added debug logging
- `app/services/rag/retriever.py` - Enhanced logging
- `app/schemas/citation.py` - Added camelCase aliases
- `app/schemas/chat.py` - Configured response serialization
- `app/routers/chat.py` - Added by_alias serialization
- `app/main.py` - Configured logging levels

**Data Pipeline:**
- `data/scripts/process_hadith.py` - Fixed field mapping
- `data/scripts/download_fiqh_v2.py` - New enhanced fiqh downloader
- `data/processed/hadith/hadith_chunks.json` - Re-generated with text
- `data/processed/fiqh/fiqh_chunks.json` - Expanded to 13 rulings

---

## ✅ RESOLVED: Issue 6 - Quran Chunks Missing Translation Text
**Problem:** All 8,351 Quran chunks had empty `text_translation` fields, only containing ayah references (e.g., "Surah Al-Fatihah (1:1)") without actual verse content
**Root Cause:** Tanzil.net XML translation files use Windows CRLF line endings with XML comments containing `#` characters, which caused Python's `xml.etree.ElementTree` parser to fail silently
**Impact:** Quranic queries returned no results because embeddings had near-zero semantic content (just surah/ayah references)
**Fix Applied:**
- Modified `data/scripts/process_quran.py` parser to:
  1. Read XML files as strings instead of parsing directly
  2. Normalize CRLF to LF line endings
  3. Strip problematic XML comment blocks using regex
  4. Parse cleaned content with `ET.fromstring()`
- Re-processed all Quran chunks:
  - 6,236 individual ayah chunks (single ayah with bilingual translations)
  - 2,115 grouped chunks (3 ayahs per chunk for better context)
- Deleted old embeddings and regenerated all 8,351 Quran chunks with full semantic content
**Files:** `data/scripts/process_quran.py` (lines 157-171), `data/processed/quran/` (all files re-generated)
**Status:** ✅ FIXED - Quranic queries now retrieve correctly with full bilingual text (Basmeih Malay + Sahih International English)
**Testing:** Verified retrieval works for both direct queries ("Bismillah") and semantic queries ("patience") with proper scoring

---

### Next Steps (Future Sessions)
1. **Tune Similarity Thresholds** - Test different thresholds per source type
2. **Expand Fiqh Dataset** - Scrape Malaysian Islamic portals (JAKIM, Mufti WP)
3. **Fix Topic Classification** - Refine classifier to avoid incorrect disclaimer triggers
4. **Add Query Rewriting** - Improve question understanding for better retrieval
5. **Implement Re-ranking** - Use cross-encoder for better relevance scoring
6. **Consider Source-Weighted Retrieval** - Balance retrieval across Quran, Hadith, Fiqh instead of pure similarity scoring
