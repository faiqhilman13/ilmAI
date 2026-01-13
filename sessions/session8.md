# Session 8 — Performance Optimizations for High Concurrency

**Date:** January 13, 2026

## Goal

Analyze and improve the backend's ability to handle 100+ concurrent requests to the `/api/chat` endpoint without crashing or severe degradation.

## Problem Analysis

Before optimization, the system had several bottlenecks:

| Bottleneck | Original State | Impact |
|------------|----------------|--------|
| DB Connection Pool | 5 + 10 overflow = 15 max | 100+ requests exhaust pool |
| LLM API Calls | 4-7 calls per request | 600+ API calls for 100 requests |
| Thread Pool | ~32 threads | Cross-encoder blocks threads |
| Concurrency Control | None | Thundering herd problem |
| Rate Limiting | None | No protection from abuse |
| Embedding Cache | None | Redundant API calls |
| Circuit Breaker | None | Cascading failures |

## What We Did

### 1. Database Connection Pool (`backend/app/core/database.py`)
- Increased `pool_size`: 5 → 20
- Increased `max_overflow`: 10 → 30
- Added `pool_timeout`: 30 seconds
- Added `pool_recycle`: 1800 seconds (30 min)
- **Result**: 50 max concurrent connections (was 15)

### 2. Settings Cache (`backend/app/config.py`)
- Added `@lru_cache(maxsize=1)` to `get_settings()`
- **Result**: Settings loaded once, not on every call

### 3. Concurrency Limiter (`backend/app/core/concurrency.py`)
- New module with asyncio Semaphore
- Limits concurrent RAG operations to 20
- 30-second timeout with 503 response if overloaded
- Applied to `/api/chat` and `/api/chat/stream` endpoints
- **Result**: Graceful queuing instead of crashes

### 4. Rate Limiting (`backend/app/core/rate_limiter.py`)
- Redis-based sliding window rate limiting
- Per-user/IP limits:
  - 30 requests per minute
  - 5 requests per 10 seconds (burst protection)
- Returns 429 with Retry-After header when exceeded
- **Result**: Protection from abuse and thundering herd

### 5. Embedding Cache (`backend/app/core/embedding_cache.py`)
- Redis cache for query embeddings
- 24-hour TTL
- MD5 hash keys for efficient storage
- Integrated into `retriever.py` via `get_or_compute_embedding()`
- **Result**: Repeated queries skip OpenAI embedding API

### 6. Circuit Breaker (`backend/app/core/circuit_breaker.py`)
- Custom async circuit breaker implementation
- States: CLOSED → OPEN → HALF_OPEN → CLOSED
- Configuration: 5 failures to open, 60s recovery timeout
- Applied to OpenAI and Anthropic API calls
- **Result**: Fast-fail when external APIs are down

### 7. Async Job Queue (`backend/app/core/job_queue.py`)
- Redis-based job queue for background processing
- New endpoints:
  - `POST /api/chat/async` - Submit job, get ID immediately
  - `GET /api/chat/job/{job_id}` - Poll for result
- Jobs expire after 1 hour
- **Result**: Non-blocking option for high-traffic scenarios

### 8. Status Endpoint (`backend/app/routers/chat.py`)
- Enhanced `GET /api/chat/status` endpoint
- Returns:
  - Queue status (available slots, in-use count)
  - Circuit breaker states for all services
- **Result**: Real-time monitoring of system health

### 9. Cross-Encoder Batching (`backend/app/services/rag/reranker.py`)
- Process chunks in batches of 32
- **Result**: Better memory management under load

### 10. LLM Client Singleton
- Already implemented with `@lru_cache` in `factory.py`
- Verified no changes needed

## Files Changed

```
backend/app/config.py                        |  19 +-
backend/app/core/circuit_breaker.py          | 186 +++++ (new)
backend/app/core/concurrency.py              |  77 ++ (new)
backend/app/core/database.py                 |   8 +-
backend/app/core/embedding_cache.py          | 148 ++++ (new)
backend/app/core/job_queue.py                | 221 +++++ (new)
backend/app/core/rate_limiter.py             | 139 +++ (new)
backend/app/routers/chat.py                  | 163 +++-
backend/app/services/llm/anthropic_client.py |  14 +-
backend/app/services/llm/openai_client.py    |  13 +-
backend/app/services/rag/reranker.py         |  20 +-
backend/app/services/rag/retriever.py        |   7 +-
backend/app/eval/                            | 350 +++++ (new, was missing)
```

## New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/status` | GET | Queue and circuit breaker status |
| `/api/chat/async` | POST | Submit message for async processing |
| `/api/chat/job/{job_id}` | GET | Poll for async job result |

## Expected Capacity

| Metric | Before | After |
|--------|--------|-------|
| Max concurrent DB connections | 15 | 50 |
| Max concurrent RAG operations | Unlimited (crash) | 20 (queued) |
| Rate limit per user | None | 30/min + 5/10s burst |
| Embedding API calls | Every query | Cached 24h |
| External API failure handling | Retry only | Circuit breaker (60s recovery) |
| Estimated concurrent capacity | ~15-20 | 50-80 |

## Deployment

1. Pushed changes to GitHub
2. SSH into VPS: `ssh -i ~/.ssh/ilmuai_hetzner root@46.224.20.19`
3. Pulled changes: `cd /opt/ilmuai && git pull`
4. Restarted backend in tmux:
   ```bash
   export TERM=xterm-256color
   tmux kill-session -t ilmuai
   tmux new -d -s ilmuai 'bash -lc "cd /opt/ilmuai/backend && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000"'
   ```
5. Verified health: `curl -s http://127.0.0.1:8000/health`

## Gotchas Encountered

1. **Terminal compatibility**: `xterm-ghostty` not recognized on VPS
   - Fix: `export TERM=xterm-256color` before tmux commands

2. **Missing eval module**: `app.eval` wasn't committed
   - Fix: Committed and pushed `backend/app/eval/` directory

## Testing

To test concurrent handling:
1. Open multiple browser tabs/devices
2. Send messages simultaneously
3. Monitor with: `curl -s https://46.224.20.19.sslip.io/api/chat/status | jq`

## What's Next

1. **Load testing**: Use tools like `locust` or `k6` to verify 50+ concurrent requests
2. **Monitoring**: Add Prometheus metrics for production observability
3. **Auto-scaling**: Consider multiple uvicorn workers or gunicorn
4. **Redis cluster**: If rate limiting becomes a bottleneck
5. **CDN**: Cache static assets and reduce origin load
