# IlmuAI

AI-powered Islamic knowledge platform for Malaysian Muslims with RAG-based Q&A, mandatory citations, and multi-language support.

## Features

- **Conversational Q&A** - Ask questions about Islam in natural language
- **RAG-Powered Answers** - Responses grounded in authentic sources (Quran, Hadith, Fiqh)
- **Mandatory Citations** - Every factual claim includes source references
- **Multi-language** - Bahasa Malaysia (primary) and English
- **Safety Layer** - Topic classification and disclaimers for sensitive subjects
- **Switchable LLM** - Support for both OpenAI and Anthropic Claude

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React + TypeScript + Vite
- **Database:** PostgreSQL with pgvector
- **Cache:** Redis
- **LLM:** OpenAI GPT-4 / Anthropic Claude (switchable)

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- OpenAI API key (and/or Anthropic API key)

### 1. Clone and Setup

```bash
cd /Users/faiqhilman/Projects/ilmuai
```

### 2. Start Infrastructure

```bash
cd docker
docker-compose up -d
```

This starts PostgreSQL (with pgvector) and Redis.

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your API keys

# Start the server
uvicorn app.main:app --reload
```

Backend will be running at http://localhost:8000

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start dev server
npm run dev
```

Frontend will be running at http://localhost:5173

## Project Structure

```
ilmuai/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Business logic (LLM, RAG, Safety)
│   │   ├── models/    # SQLAlchemy models
│   │   └── schemas/   # Pydantic schemas
│   ├── sql/           # Database schema
│   └── scripts/       # Data processing scripts
├── frontend/          # React application
│   └── src/
│       ├── components/  # UI components
│       ├── pages/       # Page components
│       ├── services/    # API clients
│       └── stores/      # Zustand stores
├── docker/            # Docker configuration
└── data/              # Islamic knowledge data
```

## Environment Variables

### Backend (.env)

```env
LLM_PROVIDER=openai           # or 'anthropic'
OPENAI_API_KEY=sk-...
# Optional: set if your key belongs to multiple orgs/projects
OPENAI_ORG_ID=org_...
OPENAI_PROJECT_ID=proj_...
ANTHROPIC_API_KEY=sk-ant-...  # Optional if using OpenAI
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ilmuai
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Next Steps

1. **Data Pipeline** - Process and embed Islamic knowledge sources
2. **Testing** - Add unit and integration tests
3. **Mobile App** - React Native version
4. **Scholar Review** - Get content validated by Islamic scholars

## License

Private - All rights reserved

---

_Bismillah. Let's build something that matters._
