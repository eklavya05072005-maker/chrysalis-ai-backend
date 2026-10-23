"""End-to-end integration test suite for Chrysalis AI backend.

Validates:
- Health and diagnostic endpoints
- PDF upload, magic header validation, and text extraction with page markers
- StorageService safe paths, directory containment, and ZIP package security
- Full 10-step Chrysalis AI workflow lifecycle:
  1. PDF upload & project creation
  2. Document text extraction & page reference preservation
  3. Requirement analysis & evidence verification (Module A)
  4. Task classification into deterministic, ai_assisted, agentic (Module B)
  5. Architecture search with 3 distinct candidates (Module C)
  6. Transparent evaluation & scenario simulation across canonical categories (Modules D & E)
  7. Architecture selection
  8. Project file generation (Module F)
  9. Safe non-executing static AST validation (Module G)
  10. Downloadable ZIP archive packaging with secrets & venv exclusion
- Error handling, guardrails, and validation status honesty
"""

import io
import os
import uuid
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import UploadFile, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import get_settings
from backend.app.db.database import get_db, Base, check_db_connectivity
from backend.app.db.models import Project
from backend.app.main import app
from backend.app.services.document_service import DocumentService
from backend.app.services.storage_service import StorageService
from backend.app.services.validation_service import ValidationService
from backend.app.integrations.llm_client import MockLLMClient
from backend.app.services.ai_engine import IntegratedAIEngine, get_ai_engine


# A well-formed PDF bytes constant with valid '%PDF-1.4' header and text
SAMPLE_SPEC_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 120 >> stream
BT
/F1 12 Tf
72 700 Td
(Chrysalis AI Specification: Autonomous Workflow Orchestration Middleware.) Tj
0 -20 Td
(System must safely coordinate tasks and validate code output.) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000415 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
488
%%EOF
"""

# Isolated SQLite test database for ultra-fast, 100% offline deterministic test runs
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def client(mock_llm_client: MockLLMClient):
    """TestClient instance configured with isolated in-memory DB and MockLLMClient."""
    # Ensure tables are created on test_engine
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    test_ai_engine = IntegratedAIEngine(llm_client=mock_llm_client)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_engine] = lambda: test_ai_engine

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# 1. Health and Diagnostic Endpoints
# ============================================================================

def test_root_health_endpoint(client: TestClient):
    """Verify root /health endpoint contract and status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "llm_provider" in data
    assert "gemini_model" in data
    assert "version" in data


def test_api_health_endpoint(client: TestClient):
    """Verify /api/health endpoint reporting database connectivity and version."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert "status" in data["database"]
    assert "version" in data


# ============================================================================
# 2. DocumentService PDF Validation and Extraction
# ============================================================================

def test_document_service_pdf_extraction_with_page_markers():
    """Verify that DocumentService successfully parses valid PDF bytes and preserves page numbers."""
    text, pages = DocumentService.extract_text_from_pdf(SAMPLE_SPEC_PDF_BYTES)
    assert len(pages) >= 1
    assert pages[0]["page"] == 1
    assert "Chrysalis AI Specification" in text or len(text) > 0


def test_document_service_validation_guards():
    """Verify PDF upload validation rejects non-PDF, empty, and invalid header files."""
    # Test invalid extension
    fake_file = UploadFile(filename="spec.txt", file=io.BytesIO(b"hello"))
    with pytest.raises(HTTPException) as exc:
        DocumentService.validate_pdf_upload(fake_file, b"hello")
    assert exc.value.status_code == 400

    # Test invalid magic header
    fake_pdf = UploadFile(filename="spec.pdf", file=io.BytesIO(b"NOT_A_PDF_HEADER"))
    with pytest.raises(HTTPException) as exc:
        DocumentService.validate_pdf_upload(fake_pdf, b"NOT_A_PDF_HEADER")
    assert exc.value.status_code == 400
    assert "header" in exc.value.detail.lower()

    # Test oversized content
    settings = get_settings()
    oversized = b"x" * (settings.max_upload_bytes + 10)
    fake_large = UploadFile(filename="large.pdf", file=io.BytesIO(oversized))
    with pytest.raises(HTTPException) as exc:
        DocumentService.validate_pdf_upload(fake_large, oversized)
    assert exc.value.status_code == 413


# ============================================================================
# 3. StorageService Path Traversal & ZIP Security
# ============================================================================

def test_storage_service_path_traversal_defense(tmp_path: Path):
    """Verify that StorageService blocks path traversal attempts."""
    storage = StorageService(base_dir=tmp_path)
    proj_id = uuid.uuid4()

    # Safe write works
    target_path, size = storage.save_generated_file(proj_id, "src/main.py", "print('safe')")
    assert target_path.exists()
    assert size > 0

    # Directory traversal in subpath is sanitized safely
    sanitized_path, _ = storage.save_generated_file(proj_id, "../../etc/passwd", "malicious")
    gen_dir = tmp_path / "generated" / str(proj_id)
    assert gen_dir.resolve() in sanitized_path.parents or sanitized_path.parent == gen_dir.resolve()


def test_storage_service_zip_packaging_excludes_secrets_and_venv(tmp_path: Path):
    """
    Verify that ZIP packaging packages only intended project files and
    strictly excludes .env secrets, .venv directories, and private keys.
    """
    storage = StorageService(base_dir=tmp_path)
    proj_id = uuid.uuid4()

    # 1. Create valid project source files
    storage.save_generated_file(proj_id, "README.md", "# Project Readme")
    storage.save_generated_file(proj_id, "src/app.py", "def run(): pass")

    # 2. Plant disallowed files directly in generated directory
    gen_dir = tmp_path / "generated" / str(proj_id)
    (gen_dir / ".env").write_text("SECRET_KEY=leak_me", encoding="utf-8")
    (gen_dir / ".env.local").write_text("API_KEY=leak_me", encoding="utf-8")
    (gen_dir / "private.key").write_text("PRIVATE_KEY_BYTES", encoding="utf-8")

    # Plant virtualenv folder
    venv_dir = gen_dir / ".venv" / "bin"
    venv_dir.mkdir(parents=True, exist_ok=True)
    (venv_dir / "python.exe").write_text("binary", encoding="utf-8")

    # 3. Create ZIP package
    zip_path = storage.create_zip_package(proj_id)
    assert zip_path.exists()

    # 4. Inspect ZIP entries
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()

        # Valid files must exist
        assert "README.md" in namelist
        assert "src/app.py" in namelist

        # Disallowed files must NOT exist
        assert ".env" not in namelist
        assert ".env.local" not in namelist
        assert "private.key" not in namelist
        assert not any(name.startswith(".venv") for name in namelist)

        # No path traversal entries
        assert not any(".." in name for name in namelist)
        assert not any(name.startswith("/") for name in namelist)


# ============================================================================
# 4. Full End-to-End Chrysalis AI Workflow
# ============================================================================

def test_full_chrysalis_end_to_end_workflow(client: TestClient):
    """
    Executes the complete 10-step Chrysalis AI pipeline via HTTP API:
    Upload PDF -> Analyze -> Classify -> Architecture Search (3) ->
    Simulate -> Select -> Generate Code -> AST Validate -> ZIP Download.
    """
    project_name = f"Chrysalis_E2E_{uuid.uuid4().hex[:6]}"

    # Step 1: Upload PDF and Create Project
    response = client.post(
        "/api/projects",
        data={"name": project_name, "description": "End-to-end integration test project"},
        files={"file": ("software_spec.pdf", SAMPLE_SPEC_PDF_BYTES, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    project_data = response.json()
    project_id = project_data["id"]
    assert project_data["name"] == project_name
    assert project_data["status"] == "uploaded"

    # Step 2: List Projects
    list_resp = client.get("/api/projects")
    assert list_resp.status_code == 200
    assert any(p["id"] == project_id for p in list_resp.json()["items"])

    # Step 3: Get Project Details
    detail_resp = client.get(f"/api/projects/{project_id}")
    assert detail_resp.status_code == 200
    assert len(detail_resp.json()["documents"]) == 1

    # Step 4: Extract and Analyze Requirements (Modules A & B)
    analyze_resp = client.post(f"/api/projects/{project_id}/analyze")
    assert analyze_resp.status_code == 200, analyze_resp.text
    reqs_data = analyze_resp.json()
    assert reqs_data["total"] > 0
    requirements = reqs_data["items"]

    # Verify requirements have valid classification categories and confidence scores
    for req in requirements:
        assert req["requirement_type"] in ("deterministic", "ai_assisted", "agentic", "functional", "integration", "non-functional")
        assert 0.0 <= req["confidence_score"] <= 1.0

    # Step 5: Generate 3 Architecture Options (Module C)
    arch_resp = client.post(f"/api/projects/{project_id}/architectures")
    assert arch_resp.status_code == 200, arch_resp.text
    archs_data = arch_resp.json()
    assert archs_data["total"] == 3
    architectures = archs_data["items"]

    # Verify candidate diversity (archetypes, pros, cons, costs)
    arch_names = [a["name"] for a in architectures]
    assert any("conservative" in n.lower() or "option 1" in n.lower() for n in arch_names)
    assert any("hybrid" in n.lower() or "option 2" in n.lower() for n in arch_names)
    assert any("automation" in n.lower() or "multi-agent" in n.lower() or "option 3" in n.lower() for n in arch_names)

    for a in architectures:
        assert len(a["components"]) > 0
        assert a["estimated_cost"]
        assert a["estimated_latency"]

    # Step 6: Simulate Architectures across Scenarios (Modules D & E)
    sim_resp = client.post(f"/api/projects/{project_id}/simulate")
    assert sim_resp.status_code == 200, sim_resp.text
    sims_data = sim_resp.json()
    assert sims_data["total"] > 0
    for sim in sims_data["items"]:
        assert sim["result_status"] in ("pass", "fail", "warning")
        assert sim["expected_outcome"]
        assert sim["simulated_outcome"]

    # Step 7: Select Architecture Candidate
    selected_arch_id = architectures[1]["id"]  # Select Hybrid Agentic
    select_resp = client.post(
        f"/api/projects/{project_id}/select",
        json={"architecture_id": selected_arch_id},
    )
    assert select_resp.status_code == 200, select_resp.text
    assert select_resp.json()["is_selected"] is True

    # Step 8: Generate Project Source Files (Module F)
    gen_resp = client.post(f"/api/projects/{project_id}/generate")
    assert gen_resp.status_code == 200, gen_resp.text
    gen_data = gen_resp.json()
    assert gen_data["total_files"] > 0
    assert gen_data["status"] == "generated"

    # Step 9: Validate Generated Source Files safely with AST (Module G)
    val_resp = client.post(f"/api/projects/{project_id}/validate")
    assert val_resp.status_code == 200, val_resp.text
    val_data = val_resp.json()
    assert val_data["total_files"] == gen_data["total_files"]
    assert val_data["failed_files"] == 0
    assert val_data["validation_status"] == "validated"

    # Step 10: Retrieve File Metadata
    files_resp = client.get(f"/api/projects/{project_id}/files")
    assert files_resp.status_code == 200
    assert len(files_resp.json()) == gen_data["total_files"]

    # Step 11: Download Package ZIP
    down_resp = client.get(f"/api/projects/{project_id}/download")
    assert down_resp.status_code == 200
    assert down_resp.headers["content-type"] == "application/zip"

    # Inspect downloaded ZIP
    zip_bytes = io.BytesIO(down_resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        zip_entries = zf.namelist()
        assert len(zip_entries) > 0
        assert "README.md" in zip_entries
        # Ensure no path traversal and no secrets
        assert not any(".." in entry for entry in zip_entries)
        assert not any(entry.startswith(".env") for entry in zip_entries)


# ============================================================================
# 5. Workflow Guardrails and Negative Tests
# ============================================================================

def test_workflow_premature_generation_guards(client: TestClient):
    """Verify that calling generation without analysis or selection fails gracefully."""
    random_id = uuid.uuid4()

    # 404 on non-existent project
    resp = client.get(f"/api/projects/{random_id}")
    assert resp.status_code == 404

    # Create project
    proj_name = f"Empty_Proj_{uuid.uuid4().hex[:6]}"
    create_resp = client.post(
        "/api/projects",
        data={"name": proj_name},
        files={"file": ("spec.pdf", SAMPLE_SPEC_PDF_BYTES, "application/pdf")},
    )
    assert create_resp.status_code == 201
    proj_id = create_resp.json()["id"]

    # Premature architecture generation (must analyze first)
    arch_resp = client.post(f"/api/projects/{proj_id}/architectures")
    assert arch_resp.status_code == 400
    assert "analyzed before architectures can be generated" in arch_resp.json()["detail"]

    # Premature file generation (must select architecture first)
    gen_resp = client.post(f"/api/projects/{proj_id}/generate")
    assert gen_resp.status_code == 400
    assert "must be selected" in gen_resp.json()["detail"]


def test_tier1_wizard_spec_and_verdict_workflow(client: TestClient):
    """Verify Tier 1 Core Intelligence endpoints: Wizard, Spec Confirmation, and Verdict."""
    project_name = f"Tier1_Core_Intelligence_{uuid.uuid4().hex[:6]}"
    create_resp = client.post(
        "/api/projects",
        data={"name": project_name, "description": "Tier 1 Core Intelligence verification"},
        files={"file": ("spec.pdf", SAMPLE_SPEC_PDF_BYTES, "application/pdf")},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    # 1. Generate Wizard Questionnaire
    wiz_resp = client.get(f"/api/projects/{project_id}/wizard")
    assert wiz_resp.status_code == 200, wiz_resp.text
    wiz_data = wiz_resp.json()
    assert wiz_data["project_name"] == project_name
    assert 3 <= len(wiz_data["questions"]) <= 5
    for q in wiz_data["questions"]:
        assert q["question_id"].startswith("WIZ-")
        assert len(q["options"]) >= 2
        assert q["reason"]

    # 2. Submit Wizard Answers (unconfirmed)
    first_q = wiz_data["questions"][0]
    answers_payload = {
        "project_name": project_name,
        "answers": [
            {
                "question_id": first_q["question_id"],
                "selected_option_id": first_q["options"][0]["option_id"],
                "answer_summary": first_q["options"][0]["label"],
            }
        ],
    }
    submit_resp = client.post(
        f"/api/projects/{project_id}/wizard",
        json=answers_payload,
    )
    assert submit_resp.status_code == 200, submit_resp.text
    spec_data = submit_resp.json()
    assert spec_data["confirmed_by_user"] is False
    assert first_q["question_id"] in spec_data["clarified_parameters"]

    # 3. Explicitly Confirm Specification
    confirm_resp = client.post(
        f"/api/projects/{project_id}/confirm",
        json=answers_payload,
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    confirmed_spec = confirm_resp.json()
    assert confirmed_spec["confirmed_by_user"] is True

    # 4. GET Specification
    get_spec_resp = client.get(f"/api/projects/{project_id}/spec")
    assert get_spec_resp.status_code == 200
    assert get_spec_resp.json()["confirmed_by_user"] is True

    # 5. POST Verdict Generation
    verdict_resp = client.post(f"/api/projects/{project_id}/verdict")
    assert verdict_resp.status_code == 200, verdict_resp.text
    verdict_data = verdict_resp.json()
    assert verdict_data["overall_verdict"] in ("non_agentic", "agentic", "hybrid")
    assert 0.0 <= verdict_data["confidence_score"] <= 1.0
    assert verdict_data["reasoning"]
    assert verdict_data["autonomy_boundary"]
    assert len(verdict_data["key_risks"]) >= 1

    # 6. GET Verdict Retrieval
    get_verdict_resp = client.get(f"/api/projects/{project_id}/verdict")
    assert get_verdict_resp.status_code == 200
    assert get_verdict_resp.json()["overall_verdict"] == verdict_data["overall_verdict"]


def test_phase3_sandbox_connectors_repair_and_audit_api_workflow(client: TestClient):
    """
    Executes the Phase 3 Dynamic Verification & Tool Ecosystem API lifecycle:
    Sandbox Execution -> Code Repair -> Connector Registration & Testing ->
    Approval Gating -> Audit Trail & Honest Verification Standing.
    """
    project_name = f"Phase3_E2E_{uuid.uuid4().hex[:6]}"

    # Step 1: Create project and upload specification
    create_resp = client.post(
        "/api/projects",
        data={"name": project_name, "description": "Phase 3 verification project"},
        files={"file": ("requirements.pdf", SAMPLE_SPEC_PDF_BYTES, "application/pdf")},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    # Step 1b: Analyze requirements (prerequisite for architecture generation)
    analyze_resp = client.post(f"/api/projects/{project_id}/analyze")
    assert analyze_resp.status_code == 200

    # Step 1c: Generate architectures, simulate, select candidate, and generate project source files
    arch_resp = client.post(f"/api/projects/{project_id}/architectures")
    assert arch_resp.status_code == 200
    arch_id = arch_resp.json()["items"][0]["id"]
    sim_resp = client.post(f"/api/projects/{project_id}/simulate")
    assert sim_resp.status_code == 200
    sel_resp = client.post(f"/api/projects/{project_id}/select", json={"architecture_id": arch_id})
    assert sel_resp.status_code == 200
    gen_resp = client.post(f"/api/projects/{project_id}/generate")
    assert gen_resp.status_code == 200



    # Step 2: Execute in Sandbox
    exec_resp = client.post(
        f"/api/projects/{project_id}/execute",
        json={
            "project_id": project_id,
            "test_command": "pytest",
            "runtime_override": "mock",
        },
    )
    assert exec_resp.status_code == 200, exec_resp.text
    exec_data = exec_resp.json()
    assert exec_data["status"] in ("tests_passed", "failed")
    assert exec_data["runtime"] == "mock_sandbox"
    run_id = exec_data["run_id"]

    # Step 3: Get Execution Run and List Runs
    get_run_resp = client.get(f"/api/projects/{project_id}/execution/{run_id}")
    assert get_run_resp.status_code == 200
    assert get_run_resp.json()["run_id"] == run_id

    list_runs_resp = client.get(f"/api/projects/{project_id}/execution")
    assert list_runs_resp.status_code == 200
    assert list_runs_resp.json()["total"] >= 1

    # Step 4: Request Bounded Code Repair
    repair_resp = client.post(
        f"/api/projects/{project_id}/repair",
        json={
            "project_id": project_id,
            "max_attempts": 1,
            "include_static_checks": True,
            "include_test_execution": True,
        },
    )
    assert repair_resp.status_code == 200, repair_resp.text
    repair_data = repair_resp.json()
    assert "total_attempts" in repair_data
    assert "final_status" in repair_data

    # Step 5: Get Repair History
    get_repair_resp = client.get(f"/api/projects/{project_id}/repair")
    assert get_repair_resp.status_code == 200
    assert get_repair_resp.json()["total_attempts"] == repair_data["total_attempts"]

    # Step 6: Register Connector
    conn_payload = {
        "connector_type": "mock",
        "name": "ERP Mock Connector",
        "is_mock": True,
        "is_read_only": True,
        "requires_approval": True,
        "allowed_endpoints": ["https://mock.erp.local/api"],
        "allowed_methods": ["GET"],
        "allowed_tools": ["search_orders"],
        "timeout_seconds": 10.0,
        "rate_limit_per_minute": 60,
        "max_response_size_kb": 1024,
        "config_data": {"api_key": "${MOCK_API_KEY}"},
    }
    conn_create_resp = client.post(
        f"/api/projects/{project_id}/connectors",
        json=conn_payload,
    )
    assert conn_create_resp.status_code == 201, conn_create_resp.text
    conn_data = conn_create_resp.json()
    connector_id = conn_data["id"]
    assert conn_data["name"] == "ERP Mock Connector"
    assert conn_data["config_data"]["api_key"] == "***REDACTED***"

    # Step 7: List Connectors
    list_conn_resp = client.get(f"/api/projects/{project_id}/connectors")
    assert list_conn_resp.status_code == 200
    assert list_conn_resp.json()["total"] >= 1

    # Step 8: Test Mock Connector
    test_conn_resp = client.post(
        f"/api/projects/{project_id}/connectors/{connector_id}/test",
        json={
            "endpoint_or_tool": "/invoices",
            "method": "GET",
            "parameters": {},
        },
    )
    assert test_conn_resp.status_code == 200, test_conn_resp.text
    test_data = test_conn_resp.json()
    assert test_data["success"] is True
    assert test_data["is_mock"] is True
    assert "sample_records" in test_data["output_data"]

    # Step 9: Approve Connector
    approve_resp = client.post(f"/api/projects/{project_id}/connectors/{connector_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["is_approved"] is True

    # Step 10: Get Honest Verification Standing and Audit Events
    audit_summary_resp = client.get(f"/api/projects/{project_id}/audit")
    assert audit_summary_resp.status_code == 200, audit_summary_resp.text
    audit_summary = audit_summary_resp.json()
    assert "verification_status" in audit_summary
    assert "active_limitations" in audit_summary
    assert len(audit_summary["active_limitations"]) >= 1

    audit_events_resp = client.get(f"/api/projects/{project_id}/audit/events")
    assert audit_events_resp.status_code == 200
    events = audit_events_resp.json()
    assert len(events) >= 1
    event_types = [e["event_type"] for e in events]
    assert "EXECUTION_RUN" in event_types or "CONNECTOR_REGISTERED" in event_types


def test_cors_preflight_and_options(client: TestClient):
    """Verifies that CORS preflight OPTIONS requests return correct CORS headers for frontend integration."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_alembic_migrations_lifecycle():
    """Verifies that all Alembic migrations apply cleanly to head and downgrade cleanly on a disposable database."""
    import tempfile, os
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import create_engine, inspect

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        url = f"sqlite:///{db_path}"
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", url)

        # 1. Upgrade to head
        command.upgrade(cfg, "head")
        eng = create_engine(url)
        insp = inspect(eng)
        tables = insp.get_table_names()

        expected_tables = {
            "projects",
            "uploaded_documents",
            "requirements",
            "architecture_options",
            "simulation_results",
            "generated_files",
            "execution_runs",
            "connectors",
            "repair_logs",
            "audit_events",
        }
        for expected in expected_tables:
            assert expected in tables, f"Table {expected} was not created by Alembic migrations."

        # 2. Downgrade to base
        command.downgrade(cfg, "base")
        insp_downgrade = inspect(eng)
        downgraded_tables = insp_downgrade.get_table_names()
        # Only alembic_version should remain
        assert len([t for t in downgraded_tables if t != "alembic_version"]) == 0

        eng.dispose()
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass


