# Enterprise Knowledge Platform (EKP)

A permission-aware Retrieval-Augmented Generation (RAG) system that allows employees to search and interact with company documents while strictly enforcing access permissions.

Company documents are indexed from local folders, with Confluence and Jira integrations planned for future releases. Employees can ask questions in natural language, and the system generates answers exclusively from documents they are authorized to access, with citations supporting every claim.

> **Status:** The core backend and frontend have been tested. Docker stack integration tests and the initial evaluation baseline are still pending. See [Known Limitations](#known-limitations) for details.

## Screenshots

_(Add screenshots of the chat interface, citations, and ACL access denial here.)_

## Key Features

- **Multi-Tenant Isolation:** Every database table and query is scoped by `tenant_id`, ensuring strict separation between organizations.
- **ACL Pre-Filtering:** Access control filters are applied directly during retrieval rather than afterward, ensuring unauthorized document chunks never appear in search results.
- **Hybrid Retrieval:** Combines BM25 keyword search and kNN vector search, merging results using Reciprocal Rank Fusion (RRF).
- **Incremental Synchronization:** Uses content hashing to process only modified documents while independently applying ACL-only changes.
- **Citation Support:** Answers include numbered citations such as `[1]` and `[2]`, with mechanisms to detect invalid or hallucinated citations.
- **Feedback Loop:** Only the query owner can submit thumbs-up or thumbs-down feedback. Negative feedback can generate candidates for the golden evaluation dataset.
- **Evaluation Gate:** Enforces thresholds for Recall, MRR, and ACL leakage. Any detected permission leak causes the evaluation gate to fail the build.

## Architecture

```text
React (Vite)  ──HTTPS + Bearer JWT──►  FastAPI (apps/api)
                                          │
                  ┌───────────────────────┼────────────────────────┐
                  ▼                       ▼                        ▼
        packages/core               OpenSearch               Postgres
   (ACL, retrieval, LLM,        (chunks + vectors +       (tenants, users,
    generation, eval)            ACL fields, alias)        documents, ACL,
                                                           versions, audit)
                  ▲
                  │ sync + index
        Celery worker (apps/worker) ◄── Redis
```

### Request Flow

Every request follows this sequence:

1. Verify the authentication token.
2. Retrieve the user, tenant, and group memberships from the database.
3. Execute BM25 and kNN retrieval with ACL filters applied.
4. Merge retrieval results using Reciprocal Rank Fusion (RRF).
5. Generate an answer with supporting citations.
6. Store an audit record for the request.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Search Engine | OpenSearch (BM25 + kNN, HNSW) |
| Database | PostgreSQL 16 |
| Background Workers | Celery + Redis |
| Frontend | React 18, Vite |
| LLM | Claude (Anthropic SDK), Fake Provider for Testing |
| Testing | pytest, Evaluation Gate Script |
| Development Infrastructure | Docker Compose |

## Repository Structure

```text
apps/api/        FastAPI: authentication, /me, /chat, /feedback
apps/worker/     Celery: sync_source task
apps/web/        React frontend
packages/core/   Shared logic: database, ACL, ingestion,
                 retrieval, LLM, generation, evaluation, feedback
eval/            Golden dataset, fixtures, evaluation runner
deploy/docker/   Docker Compose: Postgres, Redis,
                 OpenSearch, MinIO
docs/adr/        Architecture Decision Records
scripts/         Seeding, source registration, indexing helpers
```

## Quick Start (Windows PowerShell)

### Prerequisites

- Python 3.11+
- Node.js LTS
- Docker Desktop

### 1. Configure Environment

```powershell
copy .env.example .env
```

### 2. Start Infrastructure

```powershell
docker compose -f deploy/docker/docker-compose.yml up -d
```

### 3. Install Python Dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".\packages\core[dev]"
pip install -e ".\apps\api[dev]"
```

### 4. Apply Database Migrations

```powershell
cd packages\core
alembic upgrade head
cd ..\..
```

### 5. Seed Development Data

Create the initial tenant, groups, and users:

```powershell
python scripts\seed_dev.py
```

### 6. Register and Index Documents

Register a local document source with group-based access control and index its contents:

```powershell
python scripts\add_local_source.py acme "eval\fixtures\eng" --group eng
python scripts\index_source.py acme SOURCE_ID
```

### 7. Start the API Server

```powershell
cd apps\api
uvicorn app.main:app --reload --port 8000
```

### 8. Start the Frontend

Open a second terminal:

```powershell
cd apps\web
copy .env.example .env
npm install
npm run dev
```

Open the application at:

**http://localhost:5173**

Use the following development credentials:

- **Workspace:** `acme`
- **Email:** `alice@acme.test`

## Tests

Run the core package tests:

```powershell
cd packages\core
pytest -q
cd ..\..
```

Run the API tests:

```powershell
cd apps\api
pytest -q
cd ..\..
```

### Retrieval Evaluation Gate

Run the evaluation script:

```powershell
python eval\runners\run_retrieval_eval.py
```

The command reports either:

- `GATE: PASS`
- `GATE: FAIL`

A JSON evaluation report is also generated inside `eval/reports/`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | Local PostgreSQL | SQLAlchemy database connection |
| `OPENSEARCH_URL` | `http://localhost:9200` | OpenSearch endpoint |
| `JWT_SECRET` | Must be configured | JWT signing secret (32+ characters) |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins |
| `EMBEDDING_DIMENSION` | `64` | Must match the OpenSearch index mapping |
| `LLM_PROVIDER` | `fake` | Selects `fake` or `anthropic` provider |
| `LLM_MODEL` | `claude-sonnet-4-5` | Anthropic model identifier |
| `ANTHROPIC_API_KEY` | Empty | Required only when using the Anthropic provider |
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL |
| `VITE_USE_DEMO` | `true` | Set to `false` to use the real backend |

## Security Model

- **Database-Backed Permissions:** JWTs contain only the user ID and tenant information. Group memberships and account status are retrieved from the database on every request, allowing permission changes and account deactivation to take effect immediately.
- **JWT Algorithm Validation:** The accepted JWT algorithm is explicitly pinned, and tokens using `alg: none` are rejected.
- **Cross-Tenant Protection:** Cross-tenant resource requests return `not found` rather than `forbidden`, preventing unauthorized users from discovering resource existence.
- **Trusted Tenant Context:** Tenant identity is derived exclusively from the verified token, never from request bodies or headers.
- **Secure Token Storage:** Frontend authentication tokens are stored in memory rather than localStorage.
- **Safe Rendering:** AI-generated responses are rendered as plain text rather than executable HTML.

## Known Limitations

- **Embedding Model:** The current implementation uses `FakeEmbedder` with word hashing rather than semantic embeddings. Retrieval quality measurements are therefore baseline results until a real embedding model such as BGE is integrated.
- **LLM Provider:** The default provider is `fake`. The Claude provider implementation is ready, but a real end-to-end Anthropic API run has not yet been completed.
- **Docker Integration Verification:** Alembic migrations, OpenSearch integration tests, worker end-to-end execution, and the evaluation baseline are still pending.
- **Authentication:** Currently supports development-only login using email and tenant information. Production deployment requires OIDC/SSO integration.
- **Administration:** There is no dedicated API for managing users, groups, or document sources yet. Development scripts are currently used for these operations.
- **Rate Limiting and Monitoring:** Production-grade rate limiting and monitoring have not yet been implemented.
- **External Connectors:** Confluence and Jira integrations are not available yet. Currently, only the local folder connector is supported.
- **Evaluation Dataset:** The current evaluation dataset contains 10 quality test cases. A dataset of 100+ cases is needed for more reliable quality measurements.

## Roadmap

1. Complete Docker-based integration testing and establish the evaluation baseline.
2. Integrate a real embedding model and measure answer quality using Claude.
3. Add Dockerfiles and Kubernetes deployment manifests.
4. Implement Confluence and Jira document connectors.
5. Develop an administration API and integrate OIDC-based authentication.

## Author

**Umer**

This is a learning and portfolio project designed to demonstrate production-style system architecture, permission-aware retrieval, multi-tenant security, and practical RAG engineering patterns.