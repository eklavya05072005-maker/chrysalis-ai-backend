"""Pytest fixtures and configuration for Chrysalis AI offline tests."""

import pytest
from pydantic import SecretStr

from backend.app.core.config import Settings
from backend.app.integrations.llm_client import MockLLMClient
from backend.app.schemas import (
    ArchitectureArchetype,
    ArchitectureCandidate,
    ArchitectureCandidatesResult,
    ArchitectureComponent,
    ArchitectureConnection,
    ArchitectureDataFlow,
    ArchitectureEvaluationResult,
    BusinessRule,
    CandidateEvaluation,
    CheckStatus,
    CodegenManifest,
    CriterionEvaluation,
    EvidenceReference,
    GeneratedFile,
    Requirement,
    RequirementAnalysisResult,
    RiskAmbiguity,
    ScenarioCase,
    ScenarioDesignResult,
    Severity,
    SoftwareModule,
    TaskCategory,
    TaskClassification,
    TaskClassificationResult,
    TraceabilityLink,
    ValidationCheck,
    ValidationReport,
    Workflow,
    WorkflowStep,
    WizardOption,
    WizardQuestion,
    WizardQuestionnaire,
    WizardAnswer,
    WizardAnswerSubmission,
    ConfirmedProjectSpec,
    SystemVerdictType,
    SystemVerdictResult,
)


@pytest.fixture
def test_settings() -> Settings:
    """Return isolated settings for testing without relying on disk .env."""
    return Settings(
        app_name="Chrysalis Test Engine",
        environment="test",
        llm_provider="mock",
        gemini_api_key=SecretStr("test-dummy-api-key"),
        gemini_model="gemini-2.0-flash",
        llm_timeout_seconds=10.0,
        llm_temperature=0.0,
    )


@pytest.fixture
def sample_spec_text() -> str:
    """Realistic software specification excerpt for test verification."""
    return (
        "Project: FinDoc Invoice Reconciliation System\n"
        "Page 1: The system must ingest vendor invoice PDFs, extract invoice number, total amount, "
        "and line items. Rule BR-01: Any invoice exceeding $10,000 must strictly require a senior "
        "finance manager approval before payment scheduling.\n"
        "Page 2: Standard invoices under $1,000 with matching purchase orders shall be auto-reconciled "
        "via deterministic database lookup. Invoices with optical character anomalies shall be routed "
        "to an AI-assisted parsing queue. If discrepancy persists, an agentic research workflow will "
        "cross-reference vendor email correspondence."
    )


@pytest.fixture
def sample_evidence() -> EvidenceReference:
    return EvidenceReference(
        source_doc="FinDoc_Spec.pdf",
        page_number=1,
        exact_quote="Any invoice exceeding $10,000 must strictly require a senior finance manager approval before payment scheduling.",
        relevance="Directly defines human approval requirement for high-value invoice payments",
    )


@pytest.fixture
def sample_analysis_result(sample_evidence: EvidenceReference) -> RequirementAnalysisResult:
    return RequirementAnalysisResult(
        project_name="FinDoc Invoice Reconciliation System",
        executive_summary="Automated invoice ingestion, reconciliation, and payment routing system.",
        modules=[
            SoftwareModule(
                module_id="MOD-01",
                name="Ingestion & Extraction",
                responsibilities=["Ingest PDF invoices", "Extract headers and line items"],
                dependencies=["MOD-02"],
            ),
            SoftwareModule(
                module_id="MOD-02",
                name="Reconciliation Core",
                responsibilities=["Match PO numbers", "Enforce business rules"],
                dependencies=[],
            ),
        ],
        workflows=[
            Workflow(
                workflow_id="WF-01",
                name="Invoice Processing",
                trigger="Vendor uploads invoice PDF",
                steps=[
                    WorkflowStep(
                        step_number=1,
                        action="Upload PDF",
                        actor="Vendor",
                        expected_outcome="Raw PDF stored and parsed",
                    ),
                    WorkflowStep(
                        step_number=2,
                        action="Verify Line Items",
                        actor="Reconciliation Engine",
                        expected_outcome="Reconciled status or approval escalation",
                    ),
                ],
            )
        ],
        business_rules=[
            BusinessRule(
                rule_id="BR-01",
                description="Invoices exceeding $10,000 require senior finance manager approval.",
                enforcement="strict",
                evidence=[sample_evidence],
            )
        ],
        functional_requirements=[
            Requirement(
                req_id="REQ-F-01",
                title="Extract invoice fields",
                description="Extract vendor name, invoice date, total amount, and line items.",
                category="functional",
                priority="critical",
                evidence=[sample_evidence],
            )
        ],
        non_functional_requirements=[
            Requirement(
                req_id="REQ-NF-01",
                title="Processing Latency",
                description="Process standard invoices within 3 seconds.",
                category="non_functional",
                priority="high",
                evidence=[],
            )
        ],
        risks_and_ambiguities=[
            RiskAmbiguity(
                item_id="RISK-01",
                kind="risk",
                description="Corrupted or low-resolution PDF scans may degrade OCR accuracy.",
                severity=Severity.HIGH,
                mitigation_suggestion="Add fallback manual review queue for unreadable documents.",
            )
        ],
        evidence_references=[sample_evidence],
    )


@pytest.fixture
def sample_classification_result(sample_evidence: EvidenceReference) -> TaskClassificationResult:
    return TaskClassificationResult(
        classifications=[
            TaskClassification(
                task_id="BR-01",
                task_name="Rule: BR-01",
                category=TaskCategory.DETERMINISTIC,
                reasoning="Fixed mathematical comparison (amount > 10000). Predictable deterministic code.",
                supporting_evidence=[sample_evidence],
                confidence=0.99,
                risks=["Threshold definition drift"],
                human_approval_required=True,
            ),
            TaskClassification(
                task_id="REQ-F-01",
                task_name="Extract invoice fields",
                category=TaskCategory.AI_ASSISTED,
                reasoning="Unstructured OCR and entity recognition from variable PDF invoice layouts.",
                supporting_evidence=[sample_evidence],
                confidence=0.92,
                risks=["OCR hallucination", "Misaligned line items"],
                human_approval_required=False,
            ),
            TaskClassification(
                task_id="WF-01",
                task_name="Workflow: Cross-reference vendor dispute",
                category=TaskCategory.AGENTIC,
                reasoning="Dynamic multi-step investigation loop across email archives and supplier APIs.",
                supporting_evidence=[sample_evidence],
                confidence=0.86,
                risks=["Infinite tool loop", "Context limit exceeded"],
                human_approval_required=True,
            ),
        ],
        summary_counts={
            "deterministic": 1,
            "ai_assisted": 1,
            "agentic": 1,
        },
        classification_notes="Evenly distributed tasks across deterministic logic, AI parsing, and agentic research.",
    )


@pytest.fixture
def sample_architecture_candidates_result() -> ArchitectureCandidatesResult:
    return ArchitectureCandidatesResult(
        project_name="FinDoc Invoice Reconciliation System",
        candidates=[
            ArchitectureCandidate(
                candidate_id="CAND-CONSERVATIVE",
                archetype=ArchitectureArchetype.CONSERVATIVE,
                name="Deterministic Invoice Pipeline",
                summary="Robust 3-tier deterministic pipeline prioritizing predictability, low cost, and strict rule enforcement.",
                components=[
                    ArchitectureComponent(
                        component_id="COMP-API",
                        name="FastAPI Ingestion Gateway",
                        type="API Gateway",
                        responsibilities=["Ingest invoice PDFs", "Enforce input validation", "Route requests"],
                        technology_stack="Python 3.12 / FastAPI",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-RULES",
                        name="Deterministic Reconciliation Engine",
                        type="Rule Engine",
                        responsibilities=["Enforce $10k manager approval", "Execute PO lookup SQL queries"],
                        technology_stack="Python 3.12 / SQLAlchemy",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-DB",
                        name="Transactional Store",
                        type="Relational Database",
                        responsibilities=["Store invoices, purchase orders, and audit records with ACID guarantees"],
                        technology_stack="PostgreSQL 16",
                    ),
                ],
                connections=[
                    ArchitectureConnection(
                        from_component_id="COMP-API",
                        to_component_id="COMP-RULES",
                        protocol="In-Process / Synchronous",
                        description="Pass parsed invoice payload to reconciliation engine",
                    ),
                    ArchitectureConnection(
                        from_component_id="COMP-RULES",
                        to_component_id="COMP-DB",
                        protocol="SQLAlchemy Pool",
                        description="Query PO and update invoice status",
                    ),
                ],
                data_flows=[
                    ArchitectureDataFlow(
                        flow_id="FLOW-01",
                        name="Standard Reconciliation Flow",
                        steps=[
                            "User uploads invoice PDF via API Gateway",
                            "Rule Engine checks PO match and total amount",
                            "Result written to PostgreSQL database",
                        ],
                    )
                ],
                technology_assumptions=["PostgreSQL handles transactional load", "Document layouts are relatively uniform"],
                advantages=["Extremely high predictability", "Sub-100ms latency", "Lowest infrastructure cost"],
                disadvantages=["Cannot handle non-standard document variations without manual effort"],
                risks=["Rule engine bloat over time as new exception rules emerge"],
                human_approval_points=["Mandatory senior finance manager approval on invoices over $10,000"],
                estimated_cost="$40 - $70 / month (Standard VPS and managed DB)",
                estimated_latency="80ms - 150ms p95",
                complexity_score=2.5,
                complexity_definition="Standard 3-tier monolithic application with relational database and local rule evaluation.",
                quality_assumptions="Assumes 99.9% deterministic precision on structured invoices.",
            ),
            ArchitectureCandidate(
                candidate_id="CAND-HYBRID",
                archetype=ArchitectureArchetype.HYBRID_AGENTIC,
                name="Hybrid Agentic Reconciliation Platform",
                summary="Balances deterministic business logic with targeted AI parsing and an agentic vendor dispute investigator.",
                components=[
                    ArchitectureComponent(
                        component_id="COMP-API",
                        name="FastAPI Gateway",
                        type="API Gateway",
                        responsibilities=["Ingest requests", "Authenticate users"],
                        technology_stack="Python / FastAPI",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-AI-OCR",
                        name="AI-Assisted Parsing Worker",
                        type="AI Worker",
                        responsibilities=["Extract text and line items from complex invoices with vision LLM"],
                        technology_stack="Python / Gemini API",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-RULES",
                        name="Reconciliation Core",
                        type="Deterministic Service",
                        responsibilities=["Execute deterministic math and approval gates"],
                        technology_stack="Python / SQLAlchemy",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-AGENT-DISPUTE",
                        name="Vendor Research Agent",
                        type="Agentic Workflow",
                        responsibilities=["Autonomously cross-reference supplier correspondence when discrepancies occur"],
                        technology_stack="Python / Tool Registry",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-DB",
                        name="PostgreSQL Database",
                        type="Database",
                        responsibilities=["Persist data and audit trails"],
                        technology_stack="PostgreSQL",
                    ),
                ],
                connections=[
                    ArchitectureConnection(
                        from_component_id="COMP-API",
                        to_component_id="COMP-AI-OCR",
                        protocol="Async Task Queue",
                        description="Dispatch PDF to OCR worker",
                    ),
                    ArchitectureConnection(
                        from_component_id="COMP-AI-OCR",
                        to_component_id="COMP-RULES",
                        protocol="Internal REST / Queue",
                        description="Forward extracted data to rule engine",
                    ),
                    ArchitectureConnection(
                        from_component_id="COMP-RULES",
                        to_component_id="COMP-AGENT-DISPUTE",
                        protocol="Event Message",
                        description="Trigger dispute investigation on persistent mismatch",
                    ),
                ],
                data_flows=[
                    ArchitectureDataFlow(
                        flow_id="FLOW-02",
                        name="Hybrid Extraction and Dispute Flow",
                        steps=[
                            "API receives invoice PDF",
                            "AI Worker extracts fields into structured JSON",
                            "Rule Engine validates thresholds ($10k approval)",
                            "Discrepancies trigger Dispute Agent investigation",
                        ],
                    )
                ],
                technology_assumptions=["LLM available with 99.5% uptime", "Email API accessible for agent queries"],
                advantages=["High extraction accuracy across arbitrary invoice formats", "Automates dispute research", "Core money rules remain deterministic"],
                disadvantages=["Variable LLM token costs", "Higher processing latency than pure code"],
                risks=["OCR hallucination requires post-parse schema validation guardrails"],
                human_approval_points=[
                    "Senior finance manager sign-off for invoices > $10,000",
                    "Operator confirmation before dispute agent sends external emails",
                ],
                estimated_cost="$110 - $200 / month (App servers, DB, and ~10,000 invoice extraction tokens)",
                estimated_latency="450ms - 1200ms p95",
                complexity_score=5.5,
                complexity_definition="Modular service architecture combining deterministic state machines with targeted asynchronous AI workers.",
                quality_assumptions="Assumes 95% automated extraction accuracy and 80% automated dispute resolution.",
            ),
            ArchitectureCandidate(
                candidate_id="CAND-AUTOMATION",
                archetype=ArchitectureArchetype.AUTOMATION_HEAVY,
                name="Autonomous Multi-Agent Reconciliation Mesh",
                summary="Decentralized event-driven multi-agent architecture maximizing autonomous task execution with circuit breakers.",
                components=[
                    ArchitectureComponent(
                        component_id="COMP-SUPERVISOR",
                        name="Orchestrator Agent",
                        type="LLM Orchestrator",
                        responsibilities=["Decompose processing lifecycle and route to worker agents"],
                        technology_stack="Python / Multi-Agent Coordinator",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-WORKER-PARSER",
                        name="Autonomous Parser Agent",
                        type="Worker Agent",
                        responsibilities=["Adaptive tool-assisted OCR and table extraction"],
                        technology_stack="Python / Vision Tools",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-WORKER-AUDITOR",
                        name="Audit & Compliance Agent",
                        type="Worker Agent",
                        responsibilities=["Cross-reference regulatory constraints and historical vendor rates"],
                        technology_stack="Python / RAG Memory",
                    ),
                    ArchitectureComponent(
                        component_id="COMP-EVENT-BUS",
                        name="Distributed Event Stream",
                        type="Message Broker",
                        responsibilities=["Publish-subscribe message exchange and dead-letter queues"],
                        technology_stack="Apache Kafka / RabbitMQ",
                    ),
                ],
                connections=[
                    ArchitectureConnection(
                        from_component_id="COMP-SUPERVISOR",
                        to_component_id="COMP-EVENT-BUS",
                        protocol="Kafka Producer",
                        description="Broadcast task assignments",
                    ),
                    ArchitectureConnection(
                        from_component_id="COMP-EVENT-BUS",
                        to_component_id="COMP-WORKER-PARSER",
                        protocol="Consumer Group",
                        description="Deliver documents to parser agent pool",
                    ),
                ],
                data_flows=[
                    ArchitectureDataFlow(
                        flow_id="FLOW-03",
                        name="Autonomous Agentic Choreography",
                        steps=[
                            "Document published to Event Bus",
                            "Supervisor dynamically dispatches sub-agents",
                            "Auditor verifies constraints before settlement",
                            "Eventual consistency checkpoint saved",
                        ],
                    )
                ],
                technology_assumptions=["Kafka infrastructure deployed", "Agents have sandboxed tool access"],
                advantages=["Maximum autonomy", "Dynamic adaptability to brand new workflow requirements", "Self-healing tool retries"],
                disadvantages=["High operational complexity", "Significant token and infrastructure cost", "Complex distributed debugging"],
                risks=["Cascading message feedback loops", "Context window exhaustion during multi-hop reasoning"],
                human_approval_points=[
                    "Emergency circuit-breaker manual pause",
                    "Batch review for aggregate settlements exceeding $50,000",
                ],
                estimated_cost="$250 - $450 / month (Multi-agent token consumption, managed Kafka cluster, distributed tracing)",
                estimated_latency="1200ms - 3500ms p95",
                complexity_score=8.5,
                complexity_definition="Distributed event-driven choreography with multi-agent planning loops and decentralized state management.",
                quality_assumptions="Assumes 90% end-to-end autonomous resolution with 10% safety fallback rate.",
            ),
        ],
        comparison_summary="Three distinct candidates: Conservative emphasizes deterministic reliability and lowest cost; Hybrid balances deterministic rules with targeted AI/agent workers; Automation-Heavy maximizes autonomous execution with event-driven coordination.",
    )


@pytest.fixture
def sample_architecture_evaluation_result() -> ArchitectureEvaluationResult:
    return ArchitectureEvaluationResult(
        evaluations=[
            CandidateEvaluation(
                candidate_id="CAND-CONSERVATIVE",
                candidate_name="Deterministic Invoice Pipeline",
                archetype=ArchitectureArchetype.CONSERVATIVE,
                criteria_scores=[
                    CriterionEvaluation(
                        criterion_key="requirement_coverage",
                        criterion_name="Requirement Coverage",
                        raw_score=7.5,
                        weight=0.20,
                        weighted_score=1.50,
                        score_type="heuristic",
                        justification="Covers deterministic PO matching and $10k rule well, but lacks flexibility for unstructured OCR.",
                    ),
                    CriterionEvaluation(
                        criterion_key="reliability",
                        criterion_name="Reliability & Fault Tolerance",
                        raw_score=9.5,
                        weight=0.15,
                        weighted_score=1.425,
                        score_type="heuristic",
                        justification="Standard transactional RDBMS with ACID guarantees and zero non-deterministic failure modes.",
                    ),
                    CriterionEvaluation(
                        criterion_key="implementation_complexity",
                        criterion_name="Implementation Complexity & Feasibility",
                        raw_score=8.5,
                        weight=0.15,
                        weighted_score=1.275,
                        score_type="heuristic",
                        justification="Deterministically mapped from complexity score 2.5/10.0.",
                    ),
                    CriterionEvaluation(
                        criterion_key="cost",
                        criterion_name="Operating Cost Efficiency",
                        raw_score=9.0,
                        weight=0.10,
                        weighted_score=0.90,
                        score_type="estimated",
                        justification="Estimated at $40-$70/mo. No recurring LLM token consumption.",
                    ),
                    CriterionEvaluation(
                        criterion_key="latency",
                        criterion_name="Transaction Latency & Responsiveness",
                        raw_score=9.5,
                        weight=0.10,
                        weighted_score=0.95,
                        score_type="estimated",
                        justification="Sub-150ms p95 latency via in-memory rule engine and indexed PostgreSQL lookups.",
                    ),
                    CriterionEvaluation(
                        criterion_key="operational_risk",
                        criterion_name="Security & Operational Risk Mitigation",
                        raw_score=8.5,
                        weight=0.15,
                        weighted_score=1.275,
                        score_type="heuristic",
                        justification="Minimal external attack surface and established threat mitigation patterns.",
                    ),
                    CriterionEvaluation(
                        criterion_key="human_oversight",
                        criterion_name="Human Oversight & Guardrails",
                        raw_score=8.0,
                        weight=0.15,
                        weighted_score=1.20,
                        score_type="heuristic",
                        justification="Strict deterministic approval gate for all invoices exceeding $10,000.",
                    ),
                ],
                total_weighted_score=8.53,
                key_strengths=["Ultra-low latency", "Minimal operating costs", "High reliability"],
                primary_trade_offs=["Requires manual data entry for unstructured or degraded invoices"],
            ),
            CandidateEvaluation(
                candidate_id="CAND-HYBRID",
                candidate_name="Hybrid Agentic Reconciliation Platform",
                archetype=ArchitectureArchetype.HYBRID_AGENTIC,
                criteria_scores=[
                    CriterionEvaluation(
                        criterion_key="requirement_coverage",
                        criterion_name="Requirement Coverage",
                        raw_score=9.5,
                        weight=0.20,
                        weighted_score=1.90,
                        score_type="heuristic",
                        justification="Covers all requirements including unstructured extraction and automated dispute research.",
                    ),
                    CriterionEvaluation(
                        criterion_key="reliability",
                        criterion_name="Reliability & Fault Tolerance",
                        raw_score=8.5,
                        weight=0.15,
                        weighted_score=1.275,
                        score_type="heuristic",
                        justification="Decoupled queue isolates AI worker failures while core settlement remains deterministic.",
                    ),
                    CriterionEvaluation(
                        criterion_key="implementation_complexity",
                        criterion_name="Implementation Complexity & Feasibility",
                        raw_score=5.5,
                        weight=0.15,
                        weighted_score=0.825,
                        score_type="heuristic",
                        justification="Deterministically mapped from complexity score 5.5/10.0.",
                    ),
                    CriterionEvaluation(
                        criterion_key="cost",
                        criterion_name="Operating Cost Efficiency",
                        raw_score=8.0,
                        weight=0.10,
                        weighted_score=0.80,
                        score_type="estimated",
                        justification="Estimated at $110-$200/mo. Moderate LLM token costs for document extraction.",
                    ),
                    CriterionEvaluation(
                        criterion_key="latency",
                        criterion_name="Transaction Latency & Responsiveness",
                        raw_score=8.0,
                        weight=0.10,
                        weighted_score=0.80,
                        score_type="estimated",
                        justification="450ms-1200ms p95 latency due to asynchronous AI worker batching.",
                    ),
                    CriterionEvaluation(
                        criterion_key="operational_risk",
                        criterion_name="Security & Operational Risk Mitigation",
                        raw_score=8.0,
                        weight=0.15,
                        weighted_score=1.20,
                        score_type="heuristic",
                        justification="Mitigated risk with schema validation guardrails on OCR extractions.",
                    ),
                    CriterionEvaluation(
                        criterion_key="human_oversight",
                        criterion_name="Human Oversight & Guardrails",
                        raw_score=9.0,
                        weight=0.15,
                        weighted_score=1.35,
                        score_type="heuristic",
                        justification="Dual checkpoints: $10k financial sign-off and outbound email confirmation.",
                    ),
                ],
                total_weighted_score=8.15,
                key_strengths=["Balanced automation", "Strong requirement coverage", "Safe human-in-the-loop dispute handling"],
                primary_trade_offs=["Increased dependency on LLM API availability and moderate token costs"],
            ),
            CandidateEvaluation(
                candidate_id="CAND-AUTOMATION",
                candidate_name="Autonomous Multi-Agent Reconciliation Mesh",
                archetype=ArchitectureArchetype.AUTOMATION_HEAVY,
                criteria_scores=[
                    CriterionEvaluation(
                        criterion_key="requirement_coverage",
                        criterion_name="Requirement Coverage",
                        raw_score=9.0,
                        weight=0.20,
                        weighted_score=1.80,
                        score_type="heuristic",
                        justification="End-to-end automation across parsing, matching, and external supplier negotiation.",
                    ),
                    CriterionEvaluation(
                        criterion_key="reliability",
                        criterion_name="Reliability & Fault Tolerance",
                        raw_score=6.5,
                        weight=0.15,
                        weighted_score=0.975,
                        score_type="heuristic",
                        justification="Complex distributed choreography and multi-agent coordination risk cascading failures.",
                    ),
                    CriterionEvaluation(
                        criterion_key="implementation_complexity",
                        criterion_name="Implementation Complexity & Feasibility",
                        raw_score=2.5,
                        weight=0.15,
                        weighted_score=0.375,
                        score_type="heuristic",
                        justification="Deterministically mapped from complexity score 8.5/10.0.",
                    ),
                    CriterionEvaluation(
                        criterion_key="cost",
                        criterion_name="Operating Cost Efficiency",
                        raw_score=5.0,
                        weight=0.10,
                        weighted_score=0.50,
                        score_type="estimated",
                        justification="Estimated at $250-$450/mo. High token overhead from multi-turn agent loops and Kafka cluster.",
                    ),
                    CriterionEvaluation(
                        criterion_key="latency",
                        criterion_name="Transaction Latency & Responsiveness",
                        raw_score=5.5,
                        weight=0.10,
                        weighted_score=0.55,
                        score_type="estimated",
                        justification="1200ms-3500ms p95 latency due to sequential multi-agent reasoning steps.",
                    ),
                    CriterionEvaluation(
                        criterion_key="operational_risk",
                        criterion_name="Security & Operational Risk Mitigation",
                        raw_score=5.5,
                        weight=0.15,
                        weighted_score=0.825,
                        score_type="heuristic",
                        justification="Expanded attack surface with autonomous tool execution and distributed event stream.",
                    ),
                    CriterionEvaluation(
                        criterion_key="human_oversight",
                        criterion_name="Human Oversight & Guardrails",
                        raw_score=6.5,
                        weight=0.15,
                        weighted_score=0.975,
                        score_type="heuristic",
                        justification="Circuit-breaker pausing and aggregate settlement thresholds, but reduced per-invoice visibility.",
                    ),
                ],
                total_weighted_score=6.00,
                key_strengths=["Maximum autonomy and adaptable tool-augmented workflows"],
                primary_trade_offs=["High operational complexity, significant token cost, and latency overhead"],
            ),
        ],
        selected_candidate_id="CAND-CONSERVATIVE",
        selection_rationale="Deterministic Invoice Pipeline scores highest under active criteria weights due to unmatched reliability, low operational risk, and predictable cost. Note that Hybrid is superior if unstructured invoice parsing without manual entry is mandatory.",
        weights_applied={
            "requirement_coverage": 0.20,
            "reliability": 0.15,
            "implementation_complexity": 0.15,
            "cost": 0.10,
            "latency": 0.10,
            "operational_risk": 0.15,
            "human_oversight": 0.15,
        },
        methodology_notes="Scores represent transparent heuristic and estimated evaluations based on declared architectural components, complexity definitions, and stated usage assumptions. Results do not represent live benchmark measurements. The recommended candidate is identified as the highest-scoring option solely among the candidates evaluated under the active criteria weights, not a universally optimal architecture.",
    )


@pytest.fixture
def sample_scenario_design_result() -> ScenarioDesignResult:
    return ScenarioDesignResult(
        project_name="FinDoc Invoice Reconciliation System",
        scenarios=[
            ScenarioCase(
                scenario_id="SCEN-01",
                case_type="normal_workflow",
                title="Standard Invoice Ingestion & PO Reconciliation",
                description="Happy-path workflow where a standard invoice under $1,000 with a valid PO is uploaded and reconciled.",
                sample_input={
                    "invoice_id": "INV-2026-001",
                    "vendor_id": "VEND-ACME",
                    "amount": 750.00,
                    "po_number": "PO-99120",
                    "file_format": "pdf",
                },
                expected_behavior="Invoice extracted, PO matched deterministically, status set to RECONCILED without escalation.",
                evaluation_criteria=[
                    "Transaction completes within acceptable latency (<500ms)",
                    "Audit record persisted to database with correct status",
                ],
                failure_conditions=[
                    "System timeout or crash",
                    "False positive escalation to human review queue",
                ],
            ),
            ScenarioCase(
                scenario_id="SCEN-02",
                case_type="invalid_input",
                title="Corrupted PDF Binary & Schema Violation",
                description="Tests system response when an unreadable or malicious non-PDF byte stream is uploaded as an invoice.",
                sample_input={
                    "file_content": "0xDEADBEEF_CORRUPTED_STREAM",
                    "declared_mime": "application/pdf",
                    "file_size_bytes": 1024,
                },
                expected_behavior="API gateway or validator intercepts payload, returns 400 Bad Request, and aborts processing.",
                evaluation_criteria=[
                    "Descriptive error message returned to caller",
                    "Zero corrupted records written to transactional store",
                ],
                failure_conditions=[
                    "500 Internal Server Error unhandled exception",
                    "Silent pipeline failure with hanging worker process",
                ],
            ),
            ScenarioCase(
                scenario_id="SCEN-03",
                case_type="missing_information",
                title="Omission of Mandatory Purchase Order Number",
                description="Evaluates behavior when invoice layout lacks a PO number, requiring fallback investigation.",
                sample_input={
                    "invoice_id": "INV-2026-003",
                    "vendor_id": "VEND-BETA",
                    "amount": 1200.00,
                    "po_number": None,
                    "line_items": ["Office Supplies Widget A"],
                },
                expected_behavior="Detects missing mandatory PO, flags as UNMATCHED_PO, routes to exception queue or dispute agent.",
                evaluation_criteria=[
                    "Halts automated payment scheduling immediately",
                    "Emits specific missing-field diagnostic in audit trail",
                ],
                failure_conditions=[
                    "Automatic payment settlement without valid PO",
                    "Null pointer exception during database matching",
                ],
            ),
            ScenarioCase(
                scenario_id="SCEN-04",
                case_type="external_tool_failure",
                title="Downstream OCR Extraction Microservice 504 Timeout",
                description="Simulates OCR service timeout during high traffic or vendor service disruption.",
                sample_input={
                    "target_service": "ocr_extraction_worker",
                    "simulated_error": "504_GATEWAY_TIMEOUT",
                    "invoice_id": "INV-2026-004",
                },
                expected_behavior="Applies exponential retry backoff, trips circuit breaker if persistent, and enqueues to dead-letter queue.",
                evaluation_criteria=[
                    "Circuit breaker prevents cascading thread pool exhaustion",
                    "Job persisted in recovery queue without data loss",
                ],
                failure_conditions=[
                    "Indefinite thread blocking or memory leak",
                    "Unrecoverable transaction drop",
                ],
            ),
            ScenarioCase(
                scenario_id="SCEN-05",
                case_type="low_confidence_ai",
                title="Optical Character Ambiguity on Disputed Line Items",
                description="Low-resolution scan yields low confidence score (0.42) on extracted total amount.",
                sample_input={
                    "raw_ocr_score": 0.42,
                    "confidence_threshold": 0.85,
                    "inferred_amount": "1?00.00",
                    "vendor_candidate": "Global Logist?cs",
                },
                expected_behavior="Low confidence flag quarantines invoice and prompts human reviewer before reconciliation.",
                evaluation_criteria=[
                    "Automated approval prevented when confidence < 0.85",
                    "Audit log records low confidence extraction reasoning",
                ],
                failure_conditions=[
                    "Automated settlement using unverified optical inference",
                    "Undetected hallucinated invoice total",
                ],
            ),
            ScenarioCase(
                scenario_id="SCEN-06",
                case_type="sensitive_human_approval",
                title="High-Value Invoice Exceeding $10,000 Manager Approval",
                description="Invoice with amount $45,000 requires strict senior finance manager approval per rule BR-01.",
                sample_input={
                    "invoice_id": "INV-2026-006",
                    "amount": 45000.00,
                    "po_number": "PO-88192",
                    "vendor_id": "VEND-ENTERPRISE",
                },
                expected_behavior="System verifies PO, freezes payment authorization, registers pending approval, and alerts manager.",
                evaluation_criteria=[
                    "Payment strictly blocked until verified manager approval received",
                    "Audit trail records timestamp and required reviewer role",
                ],
                failure_conditions=[
                    "Automated payment release without human authorization signature",
                    "Bypass of rule BR-01 by agent or autonomous worker",
                ],
            ),
        ],
        benchmarking_guide=(
            "Benchmark Guide for Member 2 Simulation Engine: Execute each scenario against Candidate 1 (Conservative), "
            "Candidate 2 (Hybrid Agentic), and Candidate 3 (Automation-Heavy). Compare behavior on error containment, "
            "latency degradation, and human oversight enforcement."
        ),
    )


@pytest.fixture
def sample_codegen_manifest() -> CodegenManifest:
    return CodegenManifest(
        project_name="FinDoc Invoice Reconciliation System",
        archetype=ArchitectureArchetype.CONSERVATIVE,
        target_stack="Python 3.12+ / FastAPI / Pydantic / SQLAlchemy",
        files=[
            GeneratedFile(
                relative_path="requirements.txt",
                content="fastapi>=0.115.0\nuvicorn[standard]>=0.32.0\npydantic>=2.10.0\npydantic-settings>=2.6.0\npytest>=8.0.0\n",
                language="text",
                purpose="Project dependency specification",
            ),
            GeneratedFile(
                relative_path=".env.example",
                content="APP_NAME=FinDoc Invoice Reconciliation System\nENVIRONMENT=development\nDATABASE_URL=sqlite:///./findoc.db\nSENIOR_MANAGER_APPROVAL_THRESHOLD=10000.00\n",
                language="text",
                purpose="Safe environment configuration template with non-sensitive placeholders",
            ),
            GeneratedFile(
                relative_path="app/__init__.py",
                content='"""FinDoc Invoice Reconciliation System application package."""\n',
                language="python",
                purpose="Application package initializer",
            ),
            GeneratedFile(
                relative_path="app/schemas.py",
                content=(
                    '"""Pydantic data schemas for invoice reconciliation."""\n'
                    "from pydantic import BaseModel, Field\n\n"
                    "class InvoiceRequest(BaseModel):\n"
                    "    invoice_id: str\n"
                    "    vendor_id: str\n"
                    "    amount: float = Field(..., gt=0.0)\n"
                    "    po_number: str | None = None\n\n"
                    "class InvoiceResponse(BaseModel):\n"
                    "    invoice_id: str\n"
                    "    status: str\n"
                    "    requires_manager_approval: bool\n"
                    "    message: str\n"
                ),
                language="python",
                purpose="Data transfer objects and request/response models",
            ),
            GeneratedFile(
                relative_path="app/services.py",
                content=(
                    '"""Core deterministic reconciliation engine implementing Rule BR-01."""\n'
                    "from app.schemas import InvoiceRequest, InvoiceResponse\n\n"
                    "MANAGER_APPROVAL_THRESHOLD = 10000.00\n\n"
                    "def reconcile_invoice(invoice: InvoiceRequest) -> InvoiceResponse:\n"
                    '    """Enforce Rule BR-01: Invoices over $10,000 require senior manager approval."""\n'
                    "    requires_approval = invoice.amount > MANAGER_APPROVAL_THRESHOLD\n"
                    "    if requires_approval:\n"
                    '        status = "PENDING_APPROVAL"\n'
                    '        message = f"Amount ${invoice.amount:.2f} exceeds threshold ${MANAGER_APPROVAL_THRESHOLD:.2f}. Senior manager sign-off required."\n'
                    "    else:\n"
                    '        status = "RECONCILED"\n'
                    '        message = f"Invoice {invoice.invoice_id} successfully reconciled."\n'
                    "    return InvoiceResponse(\n"
                    "        invoice_id=invoice.invoice_id,\n"
                    "        status=status,\n"
                    "        requires_manager_approval=requires_approval,\n"
                    "        message=message,\n"
                    "    )\n"
                ),
                language="python",
                purpose="Deterministic business logic and approval threshold gate",
            ),
            GeneratedFile(
                relative_path="app/main.py",
                content=(
                    '"""FastAPI service entry point."""\n'
                    "from fastapi import FastAPI\n"
                    "from app.schemas import InvoiceRequest, InvoiceResponse\n"
                    "from app.services import reconcile_invoice\n\n"
                    'app = FastAPI(title="FinDoc Reconciliation API", version="1.0.0")\n\n'
                    '@app.get("/health")\n'
                    "def health():\n"
                    '    return {"status": "healthy", "service": "findoc-reconciliation"}\n\n'
                    '@app.post("/invoices/reconcile", response_model=InvoiceResponse)\n'
                    "def reconcile(invoice: InvoiceRequest):\n"
                    "    return reconcile_invoice(invoice)\n"
                ),
                language="python",
                purpose="FastAPI routing and HTTP endpoint handler",
            ),
            GeneratedFile(
                relative_path="tests/test_app.py",
                content=(
                    '"""Unit tests for reconciliation business rules."""\n'
                    "from app.schemas import InvoiceRequest\n"
                    "from app.services import reconcile_invoice\n\n"
                    "def test_reconcile_under_threshold():\n"
                    '    req = InvoiceRequest(invoice_id="INV-01", vendor_id="VEND-A", amount=500.0, po_number="PO-123")\n'
                    "    resp = reconcile_invoice(req)\n"
                    '    assert resp.status == "RECONCILED"\n'
                    "    assert not resp.requires_manager_approval\n\n"
                    "def test_manager_approval_over_threshold():\n"
                    '    req = InvoiceRequest(invoice_id="INV-02", vendor_id="VEND-B", amount=15000.0, po_number="PO-123")\n'
                    "    resp = reconcile_invoice(req)\n"
                    '    assert resp.status == "PENDING_APPROVAL"\n'
                    "    assert resp.requires_manager_approval\n"
                ),
                language="python",
                purpose="Unit tests verifying requirement BR-01 enforcement",
            ),
            GeneratedFile(
                relative_path="README.md",
                content=(
                    "# FinDoc Invoice Reconciliation System\n\n"
                    "Generated deterministic 3-tier service implementing automated invoice processing and Rule BR-01 ($10k approval gate).\n\n"
                    "## Setup\n"
                    "1. Install dependencies: `pip install -r requirements.txt`\n"
                    "2. Run tests: `pytest tests/`\n"
                    "3. Start API: `uvicorn app.main:app --reload`\n"
                ),
                language="markdown",
                purpose="Project documentation and setup guide",
            ),
        ],
        total_files=8,
        setup_instructions=[
            "python -m venv .venv",
            "source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate",
            "pip install -r requirements.txt",
            "pytest tests/",
            "uvicorn app.main:app --reload",
        ],
        completeness_notes="Generated complete FastAPI application, schemas, deterministic business logic, tests, and configuration templates.",
        is_fully_generated=True,
    )


@pytest.fixture
def sample_validation_report() -> ValidationReport:
    return ValidationReport(
        project_name="FinDoc Invoice Reconciliation System",
        candidate_id="CAND-CONSERVATIVE",
        overall_status=CheckStatus.PASSED,
        checks_total=7,
        checks_passed=6,
        checks_failed=0,
        checks_blocked=0,
        checks_not_run=1,
        checks=[
            ValidationCheck(
                check_id="CHK-STRUC-01",
                name="Manifest Completeness",
                category="file_structure",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.HIGH,
                message="Manifest structure verified with 8 valid unique files.",
            ),
            ValidationCheck(
                check_id="CHK-PATH-02",
                name="Path Safety & Traversal Defense",
                category="schema_validation",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.CRITICAL,
                message="All file paths strictly conform to safe relative path boundaries.",
            ),
            ValidationCheck(
                check_id="CHK-SYNTAX-03",
                name="Python AST Syntax Check",
                category="syntax_check",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.CRITICAL,
                message="All Python source files parsed cleanly with zero AST syntax errors.",
            ),
            ValidationCheck(
                check_id="CHK-SECRETS-04",
                name="Secrets & Credentials Audit",
                category="schema_validation",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.CRITICAL,
                message="Zero hardcoded credentials or API tokens detected across generated files.",
            ),
            ValidationCheck(
                check_id="CHK-TRACE-05",
                name="Requirement & Rule Traceability",
                category="traceability",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.HIGH,
                message="All functional requirements and business rules are mapped to source files.",
            ),
            ValidationCheck(
                check_id="CHK-TESTS-06",
                name="Documentation & Test Suite Presence",
                category="field_completeness",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.HIGH,
                message="Both README.md setup documentation and unit test suite are present.",
            ),
            ValidationCheck(
                check_id="CHK-EXEC-07",
                name="Dynamic Test Execution",
                category="test_execution",
                status=CheckStatus.NOT_RUN,
                severity_if_failed=Severity.INFO,
                message="Dynamic execution skipped. Chrysalis AI treats generated source code as untrusted input and performs bounded static validation only.",
            ),
        ],
        traceability_matrix=[
            TraceabilityLink(
                req_id="REQ-F-01",
                req_title="Extract invoice fields",
                mapped_component_ids=["app/schemas.py", "app/services.py"],
                status="covered",
                notes="Implemented in InvoiceRequest and InvoiceResponse schemas.",
            ),
            TraceabilityLink(
                req_id="BR-01",
                req_title="Invoices exceeding $10,000 require senior finance manager approval.",
                mapped_component_ids=["app/services.py", "tests/test_app.py"],
                status="covered",
                notes="Enforced via MANAGER_APPROVAL_THRESHOLD check in services and unit tests.",
            ),
        ],
        syntax_errors=[],
        warnings=[],
    )


@pytest.fixture
def sample_wizard_questionnaire() -> WizardQuestionnaire:
    return WizardQuestionnaire(
        project_name="FinDoc Invoice Reconciliation System",
        questions=[
            WizardQuestion(
                question_id="WIZ-01",
                category="autonomy",
                question_text="What level of autonomy is permitted for invoice reconciliation and payment dispatch?",
                options=[
                    WizardOption(
                        option_id="OPT-01-A",
                        label="Full Human Approval Required",
                        description="Every reconciliation mismatch or payment dispatch requires human manager sign-off.",
                        architectural_impact="Requires interactive approval checkpoints and audit log routing.",
                    ),
                    WizardOption(
                        option_id="OPT-01-B",
                        label="Supervised Autonomy with Thresholds",
                        description="Invoices under $10,000 auto-reconcile; higher amounts escalate to human reviewer.",
                        architectural_impact="Enables hybrid agentic supervisor with conditional gatekeeper.",
                    ),
                ],
                reason="Directly impacts decision boundaries, workflow supervisor design, and risk exposure.",
                allows_custom=True,
            ),
            WizardQuestion(
                question_id="WIZ-02",
                category="connectors",
                question_text="Which integration protocols are required for ERP and banking access?",
                options=[
                    WizardOption(
                        option_id="OPT-02-A",
                        label="REST & Webhooks Only",
                        description="Standard OpenAPI REST calls with webhook callbacks.",
                        architectural_impact="Deterministic HTTP client with retry policies.",
                    ),
                    WizardOption(
                        option_id="OPT-02-B",
                        label="Model Context Protocol (MCP) + REST",
                        description="Expose tools via MCP servers for flexible agentic tool calling.",
                        architectural_impact="Requires MCP client protocol handler and sandbox tool execution.",
                    ),
                ],
                reason="Dictates connector interfaces, tool-call orchestration, and network security posture.",
                allows_custom=True,
            ),
            WizardQuestion(
                question_id="WIZ-03",
                category="data_mode",
                question_text="How should document embeddings and vendor email discrepancies be queried?",
                options=[
                    WizardOption(
                        option_id="OPT-03-A",
                        label="Relational Database Only",
                        description="Exact SQL matching without vector embeddings.",
                        architectural_impact="Eliminates vector database dependency; strictly deterministic.",
                    ),
                    WizardOption(
                        option_id="OPT-03-B",
                        label="Hybrid Relational + Vector RAG",
                        description="PostgreSQL for transactions, pgvector for semantic correspondence search.",
                        architectural_impact="Requires vector store integration and chunking pipeline.",
                    ),
                ],
                reason="Determines persistence layer requirements and semantic retrieval complexity.",
                allows_custom=True,
            ),
        ],
        notes="Context-aware elicitation questions derived from FinDoc specification.",
    )


@pytest.fixture
def sample_wizard_submission() -> WizardAnswerSubmission:
    return WizardAnswerSubmission(
        project_name="FinDoc Invoice Reconciliation System",
        answers=[
            WizardAnswer(
                question_id="WIZ-01",
                selected_option_id="OPT-01-B",
                answer_summary="Supervised Autonomy with Thresholds ($10,000 rule)",
            ),
            WizardAnswer(
                question_id="WIZ-02",
                selected_option_id="OPT-02-B",
                answer_summary="Model Context Protocol (MCP) + REST",
            ),
            WizardAnswer(
                question_id="WIZ-03",
                selected_option_id="OPT-03-B",
                answer_summary="Hybrid Relational + Vector RAG",
            ),
        ],
    )


@pytest.fixture
def sample_confirmed_project_spec(
    sample_analysis_result: RequirementAnalysisResult,
    sample_wizard_submission: WizardAnswerSubmission,
) -> ConfirmedProjectSpec:
    from backend.app.ai.spec_confirmer import RequirementConfirmer
    confirmer = RequirementConfirmer()
    return confirmer.confirm_specification(
        analysis=sample_analysis_result,
        submission=sample_wizard_submission,
        confirmed_by_user=True,
    )


@pytest.fixture
def sample_system_verdict_result(sample_evidence: EvidenceReference) -> SystemVerdictResult:
    return SystemVerdictResult(
        project_name="FinDoc Invoice Reconciliation System",
        overall_verdict=SystemVerdictType.HYBRID,
        confidence_score=0.94,
        reasoning="The system combines strict deterministic rules (PO matching, thresholds) with AI parsing and bounded agentic research for invoice discrepancies.",
        deterministic_task_count=3,
        ai_assisted_task_count=2,
        agentic_task_count=1,
        autonomy_boundary="Autonomous actions restricted to invoices under $10,000; vendor communications and payments over $10,000 require senior finance manager approval.",
        key_risks=[
            "Unchecked autonomous financial dispatch",
            "OCR anomaly misinterpretations",
            "Third-party ERP connector timeouts",
        ],
        supporting_evidence=[sample_evidence],
        assumptions=[
            "ERP credentials and webhooks are pre-configured.",
            "Senior finance manager is available for escalations.",
        ],
        limitations=[
            "Dynamic execution of untrusted vendor scripts is strictly disallowed.",
            "No direct banking wire initiation without dual authentication.",
        ],
        recommended_next_step="Proceed to Architecture Planning with Hybrid Agentic Candidate.",
    )


@pytest.fixture
def mock_llm_client(
    sample_analysis_result: RequirementAnalysisResult,
    sample_classification_result: TaskClassificationResult,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_architecture_evaluation_result: ArchitectureEvaluationResult,
    sample_scenario_design_result: ScenarioDesignResult,
    sample_codegen_manifest: CodegenManifest,
    sample_validation_report: ValidationReport,
    sample_wizard_questionnaire: WizardQuestionnaire,
    sample_system_verdict_result: SystemVerdictResult,
) -> MockLLMClient:
    """Provide a preconfigured MockLLMClient ready for offline testing."""
    client = MockLLMClient()
    client.set_structured_response(RequirementAnalysisResult, sample_analysis_result)
    client.set_structured_response(TaskClassificationResult, sample_classification_result)
    client.set_structured_response(ArchitectureCandidatesResult, sample_architecture_candidates_result)
    client.set_structured_response(ArchitectureEvaluationResult, sample_architecture_evaluation_result)
    client.set_structured_response(ScenarioDesignResult, sample_scenario_design_result)
    client.set_structured_response(CodegenManifest, sample_codegen_manifest)
    client.set_structured_response(ValidationReport, sample_validation_report)
    client.set_structured_response(WizardQuestionnaire, sample_wizard_questionnaire)
    client.set_structured_response(SystemVerdictResult, sample_system_verdict_result)
    return client
