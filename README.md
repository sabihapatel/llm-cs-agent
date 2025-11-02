# LLM Customer Service Agent (MVP Starter)

A minimal, interview-ready starter that you can run locally with Docker Compose:
- **FastAPI** backend with streaming chat endpoints
- **Postgres + pgvector** (via ankane/pgvector image) for retrieval-ready storage
- Seed data + ingestion script
- Two example tools: `get_order_status`, `create_ticket`
- Basic guardrails stubs (PII redaction, domain checks)

## Quickstart

### 0) Prereqs
- Docker & Docker Compose installed

### 1) Clone & Configure
```bash
# copy env template
cp .env.example .env
```

### 2) Start Services
```bash
docker compose up --build
# API will be at http://localhost:8000/docs
# DB will be at localhost:5432
```

### 3) Ingest Sample KB
In a new terminal (once DB is up):
```bash
docker compose exec api python /app/ingest.py
```

### 4) Test the API
- Open http://localhost:8000/docs to try `/answer`
- For streaming test, use the provided WebSocket at `/ws/chat`

### Next Steps
- Step 2: Add real embeddings & retrieval (pgvector + model)
- Step 3: Add proper intent router + slot filling
- Step 4: Add human-handoff & metrics
- Step 5: Add React UI with citations & latency chips

## Project Layout

```
backend/
  app/
    main.py         # FastAPI app with /answer and /ws/chat
    tools.py        # Example tools
    rag.py          # Retrieval stubs
    guards.py       # PII redaction & safety stubs
    settings.py     # Config via env
    models.py       # DB helpers
  requirements.txt

data/
  kb/
    sample_faq.md
  ingest.py         # Builds table & seeds KB

eval/
  cases.json        # Placeholder for later evaluations

docker-compose.yml
.env.example
README.md
```

## Talking Points (for your interview)
- Orchestrated flow: guard → route → retrieve/tool → ground → stream
- Design for **latency** and **groundedness** (confidence gating, citations)
- Tooling vs pure chat: determinism, observability, regression tests
