# Chrysalis AI — Frontend API Contract Specification
**Frozen Baseline for Frontend Integration**

**Version:** 1.0.0
**Base URL:** `http://localhost:8000/api`
**CORS Origin Allowed:** `http://localhost:3000` (configurable via `FRONTEND_ORIGIN`)
**Specification Standard:** OpenAPI 3.1 / JSON (Accessible at `http://localhost:8000/openapi.json`)

---

## Workflow Sequence Overview

```
 1. Health Check            --> GET /api/health
 2. Create Project & PDF     --> POST /api/projects
 3. Analyze Requirements     --> POST /api/projects/{id}/analyze
 4. Adaptive Wizard          --> GET /api/projects/{id}/wizard
 5. Submit Answers           --> POST /api/projects/{id}/wizard
 6. Confirm Specification    --> POST /api/projects/{id}/confirm
 7. Get System Verdict       --> GET /api/projects/{id}/verdict (or POST /verdict)
 8. Generate Architectures   --> POST /api/projects/{id}/architectures
 9. Simulate Scenarios       --> POST /api/projects/{id}/simulate
10. Select Architecture      --> POST /api/projects/{id}/select
11. Generate Project Files   --> POST /api/projects/{id}/generate
12. Validate AST Syntax      --> POST /api/projects/{id}/validate
13. Execute in Sandbox       --> POST /api/projects/{id}/execute
14. Bounded Code Repair      --> POST /api/projects/{id}/repair
15. Manage Connectors        --> POST/GET /api/projects/{id}/connectors
16. Download Package ZIP     --> GET /api/projects/{id}/download
```

---

## Detailed Endpoint Contracts

### Stage 1: Health Checks

#### `GET /api/health`
- **Purpose**: Verifies backend readiness, database connectivity, and configured AI model.
- **Content-Type**: `application/json`
- **Request Parameters**: None.
- **Response Status**: `200 OK`
- **Response Schema (`HealthResponse`)**:
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "message": "connected"
  },
  "version": "1.0.0",
  "app_name": "Chrysalis AI Engine",
  "environment": "development",
  "llm_provider": "gemini",
  "gemini_model": "gemini-2.0-flash"
}
```

---

### Stage 2: Project & Document Creation

#### `POST /api/projects`
- **Purpose**: Creates a new project workspace and uploads the initial software specification PDF.
- **Workflow Position**: Stage 1
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `name` (string, required): Human-readable project title.
  - `description` (string, optional): Project summary or notes.
  - `file` (binary PDF file, required): Software specification document (`.pdf` extension, max 10MB, `%PDF` magic header required).
- **Response Status**: `201 Created`
- **Response Schema (`ProjectResponse`)**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Invoice Automation Middleware",
  "description": "Enterprise invoice processing system",
  "status": "uploaded",
  "error_message": null,
  "created_at": "2026-10-23T14:30:00Z",
  "updated_at": "2026-10-23T14:30:00Z"
}
```
- **Error Codes**:
  - `400 Bad Request`: File empty, missing `.pdf` extension, or invalid PDF magic bytes.
  - `413 Content Too Large`: File exceeds `MAX_UPLOAD_MB` (default 10MB).

#### `GET /api/projects`
- **Purpose**: Lists all projects with pagination.
- **Query Parameters**:
  - `page` (int, default: 1, min: 1)
  - `size` (int, default: 20, min: 1, max: 100)
- **Response Status**: `200 OK` (`ProjectListResponse`)

#### `GET /api/projects/{project_id}`
- **Purpose**: Retrieves full project detail, including attached documents, requirements, selected architecture, and generated files.
- **Response Status**: `200 OK` (`ProjectDetailResponse`), `404 Not Found`.

---

### Stage 3: Requirement Analysis

#### `POST /api/projects/{project_id}/analyze`
- **Purpose**: Parses uploaded PDF text, extracts grounded functional/non-functional requirements, and classifies tasks into deterministic, AI-assisted, and agentic.
- **Required Project State**: `uploaded` or `analyzed` (idempotent).
- **Content-Type**: `application/json` (Empty payload)
- **Response Status**: `200 OK`
- **Response Schema (`RequirementListResponse`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total": 2,
  "items": [
    {
      "id": "b3b24f46-9799-4d64-89c0-6d81260e86b2",
      "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "title": "Autonomous Dispute Triage",
      "description": "System classifies customer invoice disputes and assigns workflows.",
      "requirement_type": "agentic",
      "priority": "high",
      "confidence_score": 0.94,
      "source_page": 2,
      "evidence_text": "Disputes must be autonomously categorized by urgency.",
      "created_at": "2026-10-23T14:32:00Z"
    }
  ]
}
```

---

### Stage 4: Adaptive Requirement Wizard

#### `GET /api/projects/{project_id}/wizard`
- **Purpose**: Generates 3–5 context-aware architectural questions covering autonomy, connectors, data mode, and operational boundaries.
- **Required Project State**: Requirements analyzed.
- **Response Status**: `200 OK`
- **Response Schema (`WizardQuestionnaire`)**:
```json
{
  "project_name": "Invoice Automation Middleware",
  "questions": [
    {
      "question_id": "WIZ-01",
      "category": "autonomy",
      "question_text": "What level of autonomy is permitted for external database writes?",
      "options": [
        {
          "option_id": "OPT-01",
          "label": "Strict Human Approval",
          "description": "All database mutations require explicit operator sign-off.",
          "architectural_impact": "Enforces human-in-the-loop approval gates."
        },
        {
          "option_id": "OPT-02",
          "label": "Supervised Autonomy",
          "description": "Autonomous writes under $10,000 threshold.",
          "architectural_impact": "Enables threshold-based agent worker execution."
        }
      ],
      "reason": "Determines human approval checkpoints in generated architecture.",
      "allows_custom": true
    }
  ],
  "notes": "Context-aware questions synthesized from analyzed requirements."
}
```

#### `POST /api/projects/{project_id}/wizard`
- **Purpose**: Submits user answers to the wizard and produces an updated specification.
- **Query Parameter**: `confirm` (boolean, default: false).
- **Request Schema (`WizardAnswerSubmission`)**:
```json
{
  "answers": [
    {
      "question_id": "WIZ-01",
      "selected_option_id": "OPT-01",
      "custom_text": null
    }
  ],
  "notes": "User selected strict human approval"
}
```
- **Response Status**: `200 OK` (`ConfirmedProjectSpec`)

---

### Stage 5: Specification Confirmation

#### `POST /api/projects/{project_id}/confirm`
- **Purpose**: Explicitly locks and confirms the specification with user answers, setting `confirmed_by_user=true`.
- **Request Body**: `WizardAnswerSubmission` (optional, can be empty `{}`).
- **Response Status**: `200 OK`
- **Response Schema (`ConfirmedProjectSpec`)**:
```json
{
  "project_name": "Invoice Automation Middleware",
  "executive_summary": "Validated specification for Invoice Automation Middleware.",
  "confirmed_by_user": true,
  "functional_requirements": [],
  "non_functional_requirements": [],
  "modules": [],
  "workflows": [],
  "business_rules": [],
  "risks_and_ambiguities": [],
  "evidence_references": [],
  "clarified_parameters": {
    "WIZ-01": "Strict Human Approval"
  }
}
```

#### `GET /api/projects/{project_id}/spec`
- **Purpose**: Retrieves the currently stored specification.
- **Response Status**: `200 OK` (`ConfirmedProjectSpec`)

---

### Stage 6: System Verdict

#### `POST /api/projects/{project_id}/verdict`
- **Purpose**: Evaluates specification and produces an explainable overall system verdict: `non_agentic`, `agentic`, or `hybrid`.
- **Response Status**: `200 OK`
- **Response Schema (`SystemVerdictResult`)**:
```json
{
  "project_name": "Invoice Automation Middleware",
  "overall_verdict": "hybrid",
  "confidence_score": 0.92,
  "reasoning": "Core deterministic database operations paired with agentic dispute classification.",
  "deterministic_task_count": 3,
  "ai_assisted_task_count": 1,
  "agentic_task_count": 1,
  "autonomy_boundary": "Human approval required for financial transactions exceeding $10,000.",
  "key_risks": ["Model hallucination on ambiguous invoice lines"],
  "supporting_evidence": [],
  "assumptions": ["Standard cloud container environment"],
  "limitations": ["Prohibits uncontrolled host process execution"],
  "recommended_next_step": "Proceed to architecture exploration with Hybrid Agentic pattern."
}
```

#### `GET /api/projects/{project_id}/verdict`
- **Purpose**: Retrieves the previously computed system verdict for the project, or computes it on demand if pending.
- **Response Status**: `200 OK`
- **Response Schema (`SystemVerdictResult`)**: Same schema as `POST /api/projects/{project_id}/verdict`.

---

### Stage 7: Architecture Generation & Comparison

#### `POST /api/projects/{project_id}/architectures`
- **Purpose**: Generates exactly 3 distinct architecture candidates: Conservative, Hybrid Agentic, and Automation-Heavy.
- **Required State**: `analyzed`
- **Response Status**: `200 OK`
- **Response Schema (`ArchitectureListResponse`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total": 3,
  "items": [
    {
      "id": "e4a7852a-92e1-4562-8e12-b1086c87e145",
      "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Hybrid Agentic: Hybrid Agentic Middleware",
      "description": "Combines deterministic core services with LLM-assisted classification.",
      "components": [
        {"name": "Core Gateway", "role": "Routing", "type": "Gateway", "tech": "FastAPI"}
      ],
      "connections": [
        {"from": "Core Gateway", "to": "Agent Worker", "protocol": "HTTP", "desc": "Task dispatch"}
      ],
      "pros": ["Adaptive workflows", "Clear boundaries"],
      "cons": ["Moderate latency"],
      "risks": ["Model drift handled via schema validation"],
      "estimated_cost": "$45 - $90 / month",
      "estimated_latency": "300ms - 600ms",
      "complexity": "4.5 / 10 (Medium complexity)",
      "human_approval_required": true,
      "is_selected": false,
      "created_at": "2026-10-23T14:35:00Z"
    }
  ]
}
```

---

### Stage 8: Scenario Simulation

#### `POST /api/projects/{project_id}/simulate`
- **Purpose**: Simulates all 3 candidates across canonical scenario cases (stress, tool failure, invalid inputs).
- **Required State**: `architectures_ready`
- **Response Status**: `200 OK`
- **Response Schema (`SimulationListResponse`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total": 3,
  "items": [
    {
      "id": "d1e2f3a4-5717-4562-b3fc-2c963f66afa6",
      "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "architecture_id": "e4a7852a-92e1-4562-8e12-b1086c87e145",
      "scenario_name": "Normal Workflow: End-to-End Processing",
      "input_data": {"test_transactions": 50},
      "expected_outcome": "All transactions processed within 1000ms latency.",
      "simulated_outcome": "Simulation passed with 100% throughput.",
      "result_status": "pass",
      "metrics": {"p99_latency_ms": 380},
      "created_at": "2026-10-23T14:36:00Z"
    }
  ]
}
```

---

### Stage 9: Architecture Selection

#### `POST /api/projects/{project_id}/select`
- **Purpose**: Selects the target architecture candidate to generate source files for.
- **Request Schema (`ArchitectureSelectRequest`)**:
```json
{
  "architecture_id": "e4a7852a-92e1-4562-8e12-b1086c87e145"
}
```
- **Response Status**: `200 OK` (`ArchitectureOptionResponse` with `is_selected: true`).

---

### Stage 10: Code Generation

#### `POST /api/projects/{project_id}/generate`
- **Purpose**: Generates complete, usable project files (source code, tests, configs, README) into physical disk storage.
- **Required State**: Architecture selected.
- **Response Status**: `200 OK`
- **Response Schema (`GenerationSummaryResponse`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total_files": 4,
  "status": "generated",
  "files": [
    {
      "id": "11223344-5717-4562-b3fc-2c963f66afa6",
      "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "relative_path": "src/main.py",
      "filename": "main.py",
      "language": "python",
      "file_size": 1024,
      "validation_status": "pending",
      "created_at": "2026-10-23T14:38:00Z"
    }
  ]
}
```

---

### Stage 11: Static Output Validation

#### `POST /api/projects/{project_id}/validate`
- **Purpose**: Executes non-executing AST syntax and schema validation across all generated files without running the code.
- **Response Status**: `200 OK`
- **Response Schema (`ValidationReport`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total_files": 4,
  "passed_files": 4,
  "failed_files": 0,
  "validation_status": "validated",
  "details": [
    {
      "relative_path": "src/main.py",
      "filename": "main.py",
      "status": "passed",
      "error": null
    }
  ]
}
```

#### `GET /api/projects/{project_id}/files`
- **Purpose**: Lists metadata of all generated files.
- **Response Status**: `200 OK` (`List[GeneratedFileResponse]`).

---

### Stage 12: Restricted Execution Sandbox

#### `POST /api/projects/{project_id}/execute`
- **Purpose**: Runs generated project tests inside a restricted container sandbox with memory (512MB), CPU (1.0), and `--network none` isolation.
- **Request Schema (`ExecutionRunRequest`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "test_command": "pytest",
  "timeout_seconds": 30.0,
  "memory_limit_mb": 512,
  "cpu_limit": 1.0,
  "network_enabled": false,
  "runtime_override": "mock"
}
```
*Note: In local dev environments without Docker, set `runtime_override: "mock"` to verify deterministic test assertion parsing.*
- **Response Status**: `200 OK`
- **Response Schema (`ExecutionRunResult`)**:
```json
{
  "run_id": "aa11bb22-5717-4562-b3fc-2c963f66afa6",
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "tests_passed",
  "runtime": "mock_sandbox",
  "exit_code": 0,
  "stdout": "================ 4 passed in 0.12s ================",
  "stderr": "",
  "elapsed_time_seconds": 0.05,
  "timed_out": false,
  "resource_limit_hit": false,
  "network_isolated": true,
  "checks_performed": ["security_scans_passed", "mock_isolation_simulated", "test_assertion_evaluation"],
  "sandbox_cleaned_up": true,
  "message": "Deterministic mock test execution completed successfully with isolated assertions.",
  "created_at": "2026-10-23T14:40:00Z"
}
```

#### `GET /api/projects/{project_id}/execution/{run_id}`
- **Purpose**: Retrieves execution logs and metrics for a specific run.
- **Response Status**: `200 OK` (`ExecutionRunResult`), `404 Not Found`.

#### `GET /api/projects/{project_id}/execution`
- **Purpose**: Lists past execution runs for the project.
- **Response Status**: `200 OK` (`ExecutionListResponse`).

---

### Stage 13: Test-Guided Code Repair

#### `POST /api/projects/{project_id}/repair`
- **Purpose**: Executes a bounded code repair loop (default 1 attempt) using test failure diagnostics. Generates unified diffs, parses AST syntax, and verifies with sandbox test rerun.
- **Request Schema (`RepairRequest`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "max_attempts": 1,
  "include_static_checks": true,
  "include_test_execution": true
}
```
- **Response Status**: `200 OK`
- **Response Schema (`RepairHistoryResponse`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total_attempts": 1,
  "final_status": "tests_passed",
  "total_patches_applied": 1,
  "attempts": [
    {
      "attempt_number": 1,
      "initial_status": "failed",
      "failure_diagnostics": ["AssertionError: Condition failed in generated test"],
      "patches": [
        {
          "file_path": "tests/test_sample.py",
          "unified_diff": "--- a/tests/test_sample.py\n+++ b/tests/test_sample.py\n@@ -1,2 +1,2 @@\n-    assert False\n+    assert True",
          "status": "verified",
          "ast_syntax_valid": true,
          "secrets_detected": false
        }
      ],
      "rerun_status": "tests_passed",
      "checks_rerun": ["static_ast_syntax_check", "sandbox_test_execution"],
      "success": true,
      "summary": "Applied 1 validated patch(es); rerun verification passed."
    }
  ]
}
```

#### `GET /api/projects/{project_id}/repair`
- **Purpose**: Retrieves repair history and unified diffs.
- **Response Status**: `200 OK` (`RepairHistoryResponse`).

---

### Stage 14: Connector Management & Testing

#### `POST /api/projects/{project_id}/connectors`
- **Purpose**: Registers and validates a REST, Database, MCP, Custom, or Mock connector configuration.
- **Request Schema (`ConnectorConfigCreate`)**:
```json
{
  "connector_type": "mock",
  "name": "ERP Mock Connector",
  "is_mock": true,
  "is_read_only": true,
  "requires_approval": true,
  "allowed_endpoints": ["/invoices", "/customers"],
  "allowed_methods": ["GET"],
  "allowed_tools": ["query_invoice"],
  "timeout_seconds": 10.0,
  "rate_limit_per_minute": 60,
  "max_response_size_kb": 1024,
  "config_data": {
    "api_key": "${MOCK_API_KEY}"
  }
}
```
- **Response Status**: `201 Created`
- **Response Schema (`ConnectorConfigResponse`)**: Config data is returned with secrets masked (`***REDACTED***`).

#### `GET /api/projects/{project_id}/connectors`
- **Purpose**: Lists all configured connectors.
- **Response Status**: `200 OK` (`ConnectorListResponse`).

#### `POST /api/projects/{project_id}/connectors/{connector_id}/test`
- **Purpose**: Executes connector connectivity check or mock tool invocation.
- **Request Schema (`ConnectorTestRequest`)**:
```json
{
  "endpoint_or_tool": "/invoices",
  "method": "GET",
  "parameters": {}
}
```
- **Response Status**: `200 OK`
- **Response Schema (`ConnectorTestResponse`)**:
```json
{
  "connector_id": "c1c2c3c4-5717-4562-b3fc-2c963f66afa6",
  "success": true,
  "state": "verified",
  "is_mock": true,
  "status_code": 200,
  "output_data": {
    "sample_records": [
      {"invoice_id": "INV-1001", "amount": 450.00, "status": "APPROVED"}
    ]
  },
  "error_message": null,
  "elapsed_time_seconds": 0.02
}
```

#### `POST /api/projects/{project_id}/connectors/{connector_id}/approve`
- **Purpose**: Grants explicit human approval for write or sensitive operations.
- **Response Status**: `200 OK` (`ConnectorConfigResponse` with `is_approved: true`).

---

### Stage 15: Audit Trail & Honest Verification Standing

#### `GET /api/projects/{project_id}/audit`
- **Purpose**: Returns the honest verification standing and active limitations for the project.
- **Response Status**: `200 OK`
- **Response Schema (`ProjectVerificationSummary`)**:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "verification_status": "demo_verified",
  "static_checks_passed": true,
  "tests_passed": true,
  "live_integration_verified": false,
  "mock_execution_performed": true,
  "total_runs": 1,
  "total_repairs": 0,
  "active_limitations": [
    "Execution verification used mock sandbox mode; live container isolation not proven."
  ],
  "last_updated": "2026-10-23T14:42:00Z"
}
```

#### `GET /api/projects/{project_id}/audit/events`
- **Purpose**: Lists tamper-evident audit events (logins, uploads, generations, executions, approvals) with all secrets scrubbed.
- **Response Status**: `200 OK` (`List[AuditEventResponse]`).

---

### Stage 16: ZIP Export & Download

#### `GET /api/projects/{project_id}/download`
- **Purpose**: Downloads the complete generated software package as a ZIP archive.
- **Response Content-Type**: `application/zip`
- **Response Headers**: `Content-Disposition: attachment; filename="chrysalis_project_{id_prefix}.zip"`
- **Response Status**: `200 OK` (Binary stream), `404 Not Found` (if no files generated).
