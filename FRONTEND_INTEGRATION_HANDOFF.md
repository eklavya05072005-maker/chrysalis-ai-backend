# Chrysalis AI — Frontend Integration Handoff Guide

**Release Version:** 1.0.0
**Target Environment:** Local Development / Demonstration / Production
**Backend Host & Port:** `http://localhost:8000`
**API Route Prefix:** `/api`
**Interactive API Docs (Swagger):** `http://localhost:8000/docs`
**OpenAPI Specification:** `http://localhost:8000/openapi.json`

---

## 1. Quick Start Commands

### A. Starting the Backend Server
From the workspace root directory:
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start FastAPI application with live reload
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend will automatically start up on `http://localhost:8000`.*

### B. Database Migrations
The backend has an automated resilient fallback: if PostgreSQL is not running on port 5432, it will automatically connect to a local SQLite database at `data/chrysalis_dev.db` without crashing.

To run migrations explicitly against your active database:
```powershell
# Upgrade database to latest schema (002_phase3_tables)
alembic upgrade head
```

### C. Running Verification Tests
```powershell
# Run the complete test suite (142 tests)
.\.venv\Scripts\pytest backend\tests -v
```

---

## 2. Environment Configuration

Copy `.env.example` to `.env` in the root directory:
```bash
cp .env.example .env
```

Key environment variables:
| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `Chrysalis AI Engine` | Service application name |
| `ENVIRONMENT` | `development` | `development`, `staging`, `production`, `test` |
| `API_PORT` | `8000` | Port backend listens on |
| `API_HOST` | `0.0.0.0` | Host backend binds to |
| `API_V1_PREFIX`| `/api` | API route prefix |
| `DATABASE_URL` | `postgresql+psycopg://...` | PostgreSQL connection URL. Falls back to SQLite if unreachable |
| `FRONTEND_ORIGIN`| `http://localhost:3000` | Allowed CORS origins (comma-separated if multiple) |
| `DATA_DIR` | `./data` | Local storage root for uploads, generated files, and ZIP packages |
| `MAX_UPLOAD_MB`| `10` | Maximum upload size for specification PDFs |
| `LLM_PROVIDER` | `gemini` (or `mock`) | Use `mock` for 100% offline development without an API key |
| `GEMINI_API_KEY`| `""` | Google AI Studio Gemini API key (optional in mock mode) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Configured Gemini model identifier |

---

## 3. CORS Configuration

The backend is configured with FastAPI `CORSMiddleware` supporting:
- **Allowed Origins**: Defaults to `http://localhost:3000`. Set `FRONTEND_ORIGIN=http://localhost:3000,http://localhost:5173` to support Vite or Next.js dev servers.
- **Allowed Methods**: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `PATCH`.
- **Allowed Headers**: `*` (including `Content-Type`, `Authorization`).
- **Credentials**: `true`.

---

## 4. End-to-End Workflow Mapping for Frontend UI

| Stage | Frontend Action / Screen | HTTP Call | Expected Status |
|---|---|---|---|
| **0** | Application Init / Health Indicator | `GET /api/health` | `200 OK` |
| **1** | Project Upload Form | `POST /api/projects` (`FormData: name, description, file`) | `201 Created` |
| **2** | Requirement Analysis Screen | `POST /api/projects/{id}/analyze` | `200 OK` |
| **3** | Requirement Questionnaire | `GET /api/projects/{id}/wizard` | `200 OK` |
| **4** | Submit Answers / Confirm Spec | `POST /api/projects/{id}/confirm` (`{answers: [...]}`) | `200 OK` |
| **5** | Explainable System Verdict | `GET /api/projects/{id}/verdict` | `200 OK` |
| **6** | Architecture Generation & Comparison | `POST /api/projects/{id}/architectures` | `200 OK` |
| **7** | Scenario Stress Simulation | `POST /api/projects/{id}/simulate` | `200 OK` |
| **8** | Select Candidate Architecture | `POST /api/projects/{id}/select` (`{architecture_id: "..."}`) | `200 OK` |
| **9** | Source Code Generation | `POST /api/projects/{id}/generate` | `200 OK` |
| **10**| Static AST Syntax Validation | `POST /api/projects/{id}/validate` | `200 OK` |
| **11**| View Generated Files Code Editor | `GET /api/projects/{id}/files` | `200 OK` |
| **12**| Sandbox Test Execution | `POST /api/projects/{id}/execute` (`{test_command: "pytest"}`) | `200 OK` |
| **13**| Test-Guided Code Repair & Diffs | `POST /api/projects/{id}/repair` (`{max_attempts: 1}`) | `200 OK` |
| **14**| Connectors List & Testing | `POST/GET /api/projects/{id}/connectors` | `200 / 201` |
| **15**| Verification Standing & Audit Trail | `GET /api/projects/{id}/audit` | `200 OK` |
| **16**| Download Package ZIP | `GET /api/projects/{id}/download` | `200 (Binary)` |

---

## 5. Input Format & Upload Constraints

- **File Type**: PDF documents only (`.pdf` extension required).
- **Header Validation**: Files must start with the standard `%PDF` magic bytes. Corrupt or non-PDF files return `400 Bad Request`.
- **Max File Size**: Default is 10MB (enforced via `MAX_UPLOAD_MB`). Exceeding files return `413 Content Too Large`.
- **Page Extraction**: Automatic page extraction preserves page numbers for evidence citation links in requirements.

---

## 6. Error Handling Conventions

All API errors return consistent JSON responses:
```json
{
  "detail": "Descriptive and actionable error message explaining why the request failed."
}
```

HTTP status codes:
- `400 Bad Request`: Validation failure, empty file, or prerequisite stage missing (e.g., generating code before selecting an architecture).
- `404 Not Found`: Project ID, execution run, or file path does not exist.
- `413 Content Too Large`: Uploaded document exceeds 10MB limit.
- `500 Internal Server Error`: Unhandled server exception (logged with stack trace; does not leak secrets).
- `502 Bad Gateway`: External LLM provider timeout or unreachable upstream network error.

---

## 7. Prerequisites & Runtime Expectations

1. **Offline / Mock Mode (Default)**:
   - Does not require Docker, PostgreSQL, or a paid Gemini API key.
   - Set `runtime_override: "mock"` in sandbox execution calls.
   - Set `is_mock: true` on connector registrations to run synthetic enterprise demonstrations.
2. **Live Container Isolation Mode**:
   - Requires Docker Desktop or a Linux Docker daemon to be running.
   - Pull the container image: `docker pull python:3.11-slim`.
   - If Docker is offline, execution fails closed safely with `status: "blocked"` and clear security diagnostics.
3. **Live Gemini AI Mode**:
   - Set `GEMINI_API_KEY=your_key` in `.env`.
   - Set `LLM_PROVIDER=gemini`.
   - Uses `gemini-2.0-flash` with structured JSON parsing and retry handling.

---

## 8. Handoff Status

The Chrysalis AI backend is 100% frozen, audited, verified with 142 passing tests, and ready for frontend UI binding.
