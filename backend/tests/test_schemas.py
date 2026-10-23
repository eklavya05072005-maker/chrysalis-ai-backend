"""Unit tests for Chrysalis AI shared Pydantic data models and validation constraints."""

import pytest
from pydantic import ValidationError

from backend.app.schemas import (
    ArchitectureArchetype,
    ArchitectureCandidate,
    ArchitectureCandidatesResult,
    ArchitectureComponent,
    ArchitectureConnection,
    ArchitectureDataFlow,
    CandidateEvaluation,
    CheckStatus,
    CriterionEvaluation,
    EvidenceReference,
    GeneratedFile,
    RequirementAnalysisResult,
    ScenarioCase,
    Severity,
    TaskCategory,
    TaskClassification,
    ValidationCheck,
    ValidationReport,
)


def test_evidence_reference_valid():
    ref = EvidenceReference(
        source_doc="spec.pdf",
        page_number=3,
        exact_quote="All payment refunds must be logged.",
        relevance="Confirms audit log requirement.",
    )
    assert ref.source_doc == "spec.pdf"
    assert ref.page_number == 3
    assert "payment refunds" in ref.exact_quote


def test_evidence_reference_forbids_empty_fields():
    with pytest.raises(ValidationError):
        EvidenceReference(
            source_doc="",
            exact_quote="Quote",
            relevance="Relevance",
        )


def test_task_classification_valid():
    tc = TaskClassification(
        task_id="TASK-01",
        task_name="Calculate Tax",
        category=TaskCategory.DETERMINISTIC,
        reasoning="Standard tax table calculation with fixed statutory formulas.",
        confidence=0.99,
        risks=["Tax code formula drift"],
        human_approval_required=False,
    )
    assert tc.category == TaskCategory.DETERMINISTIC
    assert tc.human_approval_required is False


def test_architecture_candidate_complexity_bounds():
    comp = ArchitectureComponent(
        component_id="COMP-01",
        name="API Service",
        type="Deterministic Service",
        responsibilities=["Handle requests"],
        technology_stack="FastAPI",
    )
    conn = ArchitectureConnection(
        from_component_id="COMP-01",
        to_component_id="COMP-01",
        protocol="HTTP",
        description="Self loopback",
    )
    flow = ArchitectureDataFlow(
        flow_id="FLOW-01",
        name="Main Flow",
        steps=["Step 1"],
    )

    # Complexity score must be between 1.0 and 10.0
    with pytest.raises(ValidationError):
        ArchitectureCandidate(
            candidate_id="CAND-01",
            archetype=ArchitectureArchetype.CONSERVATIVE,
            name="Conservative Stack",
            summary="Reliable deterministic baseline",
            components=[comp],
            connections=[conn],
            data_flows=[flow],
            technology_assumptions=["Python"],
            advantages=["Simple"],
            disadvantages=["Manual work required"],
            risks=["Slow response"],
            estimated_cost="$50/mo",
            estimated_latency="150ms",
            complexity_score=15.0,  # Invalid: > 10.0
            complexity_definition="Exceeds scale",
        )


def test_architecture_candidates_result_requires_exactly_three():
    comp = ArchitectureComponent(
        component_id="COMP-01",
        name="API",
        type="API",
        responsibilities=["API"],
        technology_stack="Python",
    )
    conn = ArchitectureConnection(
        from_component_id="COMP-01",
        to_component_id="COMP-01",
        protocol="HTTP",
        description="Loop",
    )
    flow = ArchitectureDataFlow(flow_id="FLOW-01", name="Flow", steps=["Step"])

    def make_candidate(cand_id: str, archetype: ArchitectureArchetype):
        return ArchitectureCandidate(
            candidate_id=cand_id,
            archetype=archetype,
            name=f"{archetype.value} candidate",
            summary="Summary",
            components=[comp],
            connections=[conn],
            data_flows=[flow],
            technology_assumptions=["Python"],
            advantages=["Adv"],
            disadvantages=["Disadv"],
            risks=["Risk"],
            estimated_cost="$100",
            estimated_latency="200ms",
            complexity_score=4.0,
            complexity_definition="Standard definition",
        )

    # Only 2 candidates should fail validation
    with pytest.raises(ValidationError):
        ArchitectureCandidatesResult(
            project_name="Test Project",
            candidates=[
                make_candidate("C1", ArchitectureArchetype.CONSERVATIVE),
                make_candidate("C2", ArchitectureArchetype.HYBRID_AGENTIC),
            ],
            comparison_summary="Missing automation heavy",
        )

    # Exactly 3 candidates passes
    result = ArchitectureCandidatesResult(
        project_name="Test Project",
        candidates=[
            make_candidate("C1", ArchitectureArchetype.CONSERVATIVE),
            make_candidate("C2", ArchitectureArchetype.HYBRID_AGENTIC),
            make_candidate("C3", ArchitectureArchetype.AUTOMATION_HEAVY),
        ],
        comparison_summary="Full comparison of all 3 required archetypes",
    )
    assert len(result.candidates) == 3


def test_generated_file_path_traversal_prevention():
    # Valid relative paths should succeed
    valid_file = GeneratedFile(
        relative_path="app/routers/invoices.py",
        content="print('valid')",
        language="python",
        purpose="Router for invoices",
    )
    assert valid_file.relative_path == "app/routers/invoices.py"

    # Absolute unix paths must fail
    with pytest.raises(ValidationError):
        GeneratedFile(
            relative_path="/etc/passwd",
            content="malicious",
            purpose="test",
        )

    # Directory traversal prefix must fail
    with pytest.raises(ValidationError):
        GeneratedFile(
            relative_path="../app/main.py",
            content="malicious",
            purpose="test",
        )

    # Internal directory traversal must fail
    with pytest.raises(ValidationError):
        GeneratedFile(
            relative_path="app/../../outside.py",
            content="malicious",
            purpose="test",
        )

    # Windows drive letters must fail
    with pytest.raises(ValidationError):
        GeneratedFile(
            relative_path="C:/Windows/System32/evil.dll",
            content="malicious",
            purpose="test",
        )


def test_validation_report_status_honesty():
    check = ValidationCheck(
        check_id="CHK-01",
        name="Syntax check",
        category="syntax_check",
        status=CheckStatus.FAILED,
        severity_if_failed=Severity.CRITICAL,
        message="Syntax error in generated line 12",
    )
    report = ValidationReport(
        project_name="Test",
        candidate_id="CAND-01",
        overall_status=CheckStatus.FAILED,
        checks_total=1,
        checks_failed=1,
        checks=[check],
    )
    assert report.overall_status == CheckStatus.FAILED
    assert report.checks[0].status == CheckStatus.FAILED
