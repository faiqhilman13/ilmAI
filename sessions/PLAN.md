# IlmuAI - Development Plan & Progress

**Project:** AI-powered Islamic Knowledge Platform for Malaysian Muslims
**Last Updated:** December 11, 2024 (Session 2)

---

## Overall Progress

```
Phase 1: Foundation     [####################] 100% COMPLETE
Phase 2: Core Backend   [####################] 100% COMPLETE
Phase 3: Data Pipeline  [##########..........]  50% IN PROGRESS
Phase 4: Frontend       [################....]  80% PARTIAL
Phase 5: Polish         [....................]   0% PENDING
```

---

## Phase 1: Foundation - COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| Create monorepo structure | Done | `/Users/faiqhilman/Projects/ilmuai` |
| Docker Compose setup | Done | PostgreSQL (pgvector) + Redis |
| FastAPI app skeleton | Done | With CORS, lifespan, error handling |
| Database schema | Done | `backend/sql/schema.sql` |
| JWT authentication | Done | Register, Login, Protected routes |

---

## Phase 2: Core Backend - COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| LLM abstraction layer | Done | OpenAI + Anthropic switchable |
| Embedding service | Done | Via LLM clients |
| Knowledge retriever | Done | pgvector semantic search |
| RAG pipeline | Done | Full orchestration with prompts |
| Citation system | Done | Quran, Hadith, Fiqh, Fatwa types |
| Safety/disclaimer layer | Done | Topic classification + disclaimers |
| Chat API endpoints | Done | `/api/chat`, streaming support |

---

## Phase 3: Data Pipeline - IN PROGRESS (50%)

| Task | Status | Action Steps |
|------|--------|--------------|
| Download Quran data | Script Ready | Run `python data/scripts/download_quran.py` |
| Download Hadith data | Script Ready | Run `python data/scripts/download_hadith.py` |
| Download Fiqh data | Script Ready | Run `python data/scripts/download_fiqh.py` |
| Process Quran | Script Ready | Run `python data/scripts/process_quran.py` |
| Process Hadith | Script Ready | Run `python data/scripts/process_hadith.py` |
| Process Fiqh | Script Ready | Run `python data/scripts/process_fiqh.py` |
| Generate embeddings | Pending | 1. Create `backend/scripts/generate_embeddings.py`<br>2. Use OpenAI text-embedding-3-small<br>3. Batch process (100 at a time) |
| Seed database | Pending | 1. Insert processed chunks into `knowledge_chunks`<br>2. Verify vector search works<br>3. Test retrieval quality |

### Download Scripts Created

| Script | Location | Sources |
|--------|----------|---------|
| `download_quran.py` | `data/scripts/` | Tanzil.net (Arabic Uthmani + BM Basmeih + EN Sahih) |
| `download_hadith.py` | `data/scripts/` | GitHub datasets (6 collections), sunnah.com API optional |
| `download_fiqh.py` | `data/scripts/` | Internet Archive (Al-Fiqh Al-Manhaji JAKIM Edition) |

### Processing Scripts Created

| Script | Location | Features |
|--------|----------|----------|
| `process_quran.py` | `data/scripts/` | Parse Tanzil XML, combine Arabic + translations, individual & grouped chunks |
| `process_hadith.py` | `data/scripts/` | Parse GitHub JSON, normalize grading, extract metadata, create chunks |
| `process_fiqh.py` | `data/scripts/` | Parse sample JSON, optional PDF extraction, classify by topic |

### Data Sources

| Source | URL | Format |
|--------|-----|--------|
| Quran (Arabic) | tanzil.net/download | XML |
| Quran (BM - Basmeih) | tanzil.net/trans | XML |
| Hadith | GitHub + sunnah.com | JSON |
| Shafi'i Fiqh | archive.org/details/Fiqhmanhaji1 | PDF |
| Malaysian Fatwa | e-smaf.islam.gov.my | Web scraping |

---

## Phase 4: Frontend - 80% COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| React + Vite + TypeScript | Done | With path aliases |
| Tailwind CSS + i18n | Done | BM/EN translations |
| Chat interface | Done | ChatContainer, MessageList, etc. |
| Citation display | Done | Expandable cards for all types |
| Streaming support | Done | SSE in chatService |
| Conversation history | Partial | UI done, API integration pending |
| Bookmarks page | Pending | Component exists, page not created |
| Settings page | Pending | Not started |
| Language switcher | Done | In header |

### Remaining Frontend Tasks

1. **BookmarksPage.tsx** - Create page to list/manage bookmarks
2. **SettingsPage.tsx** - User preferences (language, madhab, theme)
3. **Conversation sidebar** - Connect to API, load real conversations
4. **Error handling** - Better error states and retry logic
5. **Mobile responsiveness** - Test and fix on mobile devices

---

## Phase 5: Polish - PENDING

| Task | Status | Action Steps |
|------|--------|--------------|
| Topic classification | Basic Done | Enhance with ML-based classification |
| Sensitivity detection | Basic Done | Add more keywords, refine thresholds |
| Disclaimer injection | Done | - |
| Error handling | Pending | 1. Add retry logic to LLM calls<br>2. Better error messages for users<br>3. Logging and monitoring |
| Testing | Pending | 1. Unit tests for RAG pipeline<br>2. Integration tests for API<br>3. E2E tests for frontend |
| Performance | Pending | 1. Add response caching (Redis)<br>2. Optimize vector search<br>3. Add rate limiting |

---

## PRD Feature Mapping

### MVP Features (Phase 1)

| PRD Feature | Implementation Status |
|-------------|----------------------|
| F1. Conversational Q&A | Complete |
| F2. RAG-Powered Retrieval | Complete (needs data) |
| F3. Mandatory Citation System | Complete |
| F4. Disclaimer & Boundary System | Complete |
| F5. Language Support (BM/EN) | Complete |
| F6. Basic User Accounts | Complete |

### Phase 2 Features (Future)

| PRD Feature | Status |
|-------------|--------|
| F7. Verified Scholar Network | Not started |
| F8. Learning Paths | Not started |
| F9. Audio Support | Not started |
| F10. Hadith Verification Tool | Partial (grading shown) |
| F11. Prayer & Ibadah Tools | Not started |

### Phase 3 Features (Future)

| PRD Feature | Status |
|-------------|--------|
| F12. JAKIM Integration | Not started |
| F13. Mosque Dashboard | Not started |
| F14. Analytics & Insights | Not started |
| F15. Multi-Mazhab Support | Not started |

---

## Immediate Next Steps

### Remaining for Data Pipeline

1. **Start Docker & verify infrastructure**
   ```bash
   cd /Users/faiqhilman/Projects/ilmuai/docker
   docker-compose up -d
   ```

2. **Download all Islamic data**
   ```bash
   cd /Users/faiqhilman/Projects/ilmuai
   python data/scripts/download_quran.py
   python data/scripts/download_hadith.py
   python data/scripts/download_fiqh.py
   ```

3. **Process downloaded data**
   ```bash
   python data/scripts/process_quran.py
   python data/scripts/process_hadith.py
   python data/scripts/process_fiqh.py
   ```

4. **Generate embeddings and seed database**
   - Create `backend/scripts/generate_embeddings.py`
   - Insert into pgvector
   - Test retrieval

5. **Test full flow**
   - Start backend
   - Start frontend
   - Ask a question
   - Verify citations appear

---

## Session Log

| Session | Date | Focus | Outcome |
|---------|------|-------|---------|
| 1 | Dec 11, 2024 | Foundation | Built full-stack skeleton (68 files), created download scripts |
| 2 | Dec 11, 2024 | Data Processing | Created 3 processing scripts for Quran, Hadith, Fiqh |
| 3 | TBD | Embeddings | Generate embeddings, seed database, test retrieval |
| 4 | TBD | Integration | End-to-end testing |
| 5 | TBD | Polish | Error handling, testing |

---

## Files Created by Session

### Session 1 (Dec 11, 2024)
- **68 core files** - Backend, Frontend, Infrastructure
- **3 download scripts:**
  - `data/scripts/download_quran.py`
  - `data/scripts/download_hadith.py`
  - `data/scripts/download_fiqh.py`

### Session 2 (Dec 11, 2024)
- **3 processing scripts:**
  - `data/scripts/process_quran.py` - Parses Tanzil XML, creates ayah chunks + grouped chunks
  - `data/scripts/process_hadith.py` - Parses hadith JSON, normalizes grading, creates chunks
  - `data/scripts/process_fiqh.py` - Parses sample fiqh JSON, optional PDF extraction

---

## Technical Debt

1. **No tests** - Need unit and integration tests
2. **No logging** - Add structured logging
3. **No monitoring** - Add health checks and metrics
4. **Hardcoded prompts** - Move to config/database
5. **No caching** - Add Redis caching for responses
6. **No rate limiting** - Add API rate limits

---

## Questions to Resolve

1. **Scholar Advisory** - Who can review content accuracy?
2. **JAKIM Contact** - How to approach for official data?
3. **Legal Structure** - Company, social enterprise, or waqf?
4. **Hosting** - AWS, Vercel, or local Malaysian provider?

---

*Plan maintained by Claude Code*
