# Email Classifier Service

## Description

REST API service that accepts an `.eml` file, parses it, and classifies the email using an LLM (Claude).
Every classification is stored in the database and can be retrieved later by its ID.
Submitting the same file twice returns the existing result without re-classifying.

- Swagger — http://localhost:8000/api/docs
- ReDoc — http://localhost:8000/api/redoc

The execution commands are stored in the `Makefile`.

## Architecture

Classification is handled **asynchronously** via a dedicated worker process rather than inside the HTTP request:

```
POST /classify/
    │
    ├── validate .eml
    ├── compute SHA-256 hash  →  duplicate? return 200 with existing record
    ├── persist record (status=pending)
    └── return 201 immediately
                │
                ▼
    [classify worker — polls every N seconds]
        ├── fetch one pending record (SELECT ... FOR UPDATE SKIP LOCKED)
        ├── parse .eml → call Anthropic Claude (tool use)
        ├── confidence ≥ 0.6  →  status=classified
        └── confidence < 0.6  →  status=pending, retry → status=classified, reviewed=true
                │
    [retry worker — polls every 10 min]
        └── reset failed → pending for re-processing
```

**Why async over synchronous classification:**

A synchronous approach (classify inside the HTTP handler) would tie up an API worker thread for the duration of the LLM call — typically 2–5 seconds. Under moderate load this leads to thread exhaustion, increased latency for all endpoints, and cascading timeouts. The async worker model decouples ingestion from classification: the API responds in milliseconds, and the worker processes records at its own pace without affecting API throughput.

**Scaling path — message broker:**

The current worker uses DB polling (`SELECT FOR UPDATE SKIP LOCKED`), which is simple and works well at low-to-medium throughput. If DB polling becomes a bottleneck at high load (many concurrent uploads, high query rate on the `classification_record` table), the classify worker can be migrated to consume from a message broker (RabbitMQ, Redis Streams) with minimal changes — the `POST /classify/` handler publishes a job instead of relying on a DB status field, and the worker subscribes to the queue. The rest of the codebase stays unchanged.

## Requirements

- Python 3.12+
- Poetry
- Docker

## Setup

1. **Clone repository:**

   ```
   git clone git@github.com:aleksandr294/email-classifier.git
   cd email-classifier
   ```

2. **Install Poetry:**

   ```
   pip install poetry
   ```

3. **Install dependencies:**

   ```
   poetry install
   ```

4. **Set .env file:**

   ```
   cp .env.example .env
   ```

   Fill in the variables:

   ```env
   POSTGRES_URL=postgresql+asyncpg://user:user@localhost:15000/test_db
   ANTHROPIC_API_KEY=your_anthropic_api_key
   LLM_MODEL_NAME=claude-haiku-4-5-20251001
   ```

5. **Start local database:**

   ```
   make up_local_environment
   ```

6. **Apply migrations:**

   ```
   make migrate
   ```

7. **Run API:**

   ```
   make run_api
   ```

8. **Run workers** (separate terminals):

   ```
   make run_classify
   make run_retry
   ```

## Run full stack (API + workers + PostgreSQL)

```
docker build -f docker/Dockerfile.base -t email-classifier-base:latest . && docker compose -f docker-compose.yml -p email-classifier-system up --build
```

## API

#### POST /api/v1/classify/
#### GET /api/v1/classify/{id}/

For detail information see Swagger

## Linters

Install pre-commit hooks:

```
pre-commit install
```

Run linters:

```
pre-commit run --all-files
```

## Tests

Run tests

```
pytest
```