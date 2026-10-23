"""Unit tests for Module G: Output Validation Engine.

All tests run statically and offline without external API calls or executing untrusted code.
"""

import pytest
from backend.app.ai.validator import OutputValidator, validate_generated_code
from backend.app.core.config import Settings
from backend.app.schemas import (
    CheckStatus,
    CodegenManifest,
    GeneratedFile,
    Requirement,
    RequirementAnalysisResult,
    Severity,
    ValidationReport,
)


def test_validate_valid_generated_project(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)
    report = validator.validate(sample_codegen_manifest, sample_analysis_result)

    assert isinstance(report, ValidationReport)
    assert report.overall_status == CheckStatus.PASSED
    assert report.checks_total == 7
    assert report.checks_passed == 6
    assert report.checks_failed == 0
    assert report.checks_blocked == 0
    assert report.checks_not_run == 1  # Dynamic test execution not run

    # Verify AST syntax check passed
    syntax_check = next(c for c in report.checks if c.check_id == "CHK-SYNTAX-03")
    assert syntax_check.status == CheckStatus.PASSED
    assert len(report.syntax_errors) == 0

    # Verify traceability
    trace_check = next(c for c in report.checks if c.check_id == "CHK-TRACE-05")
    assert trace_check.status == CheckStatus.PASSED
    assert len(report.traceability_matrix) >= 2


def test_validate_missing_or_empty_files(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)

    # Invalidate one file by emptying its content
    corrupted_files = list(sample_codegen_manifest.files)
    corrupted_files.append(
        GeneratedFile(
            relative_path="app/empty_module.py",
            content="   ",
            purpose="Testing empty file detection",
        )
    )
    manifest = CodegenManifest(
        project_name=sample_codegen_manifest.project_name,
        archetype=sample_codegen_manifest.archetype,
        files=corrupted_files,
        completeness_notes="Test manifest notes",
    )

    report = validator.validate(manifest, sample_analysis_result)
    assert report.overall_status == CheckStatus.FAILED
    assert report.checks_failed >= 1

    struc_check = next(c for c in report.checks if c.check_id == "CHK-STRUC-01")
    assert struc_check.status == CheckStatus.FAILED
    assert "Empty content detected" in struc_check.message


def test_validate_duplicate_and_unsafe_paths(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)

    # 1. Duplicate paths
    dup_files = list(sample_codegen_manifest.files)
    dup_files.append(
        GeneratedFile(
            relative_path="requirements.txt",  # Duplicate of existing
            content="pytest>=8.0.0\n",
            purpose="Duplicate file",
        )
    )
    dup_manifest = CodegenManifest.model_construct(
        project_name="Dup Project",
        archetype=sample_codegen_manifest.archetype,
        files=dup_files,
    )

    dup_report = validator.validate(dup_manifest, sample_analysis_result)
    assert dup_report.overall_status == CheckStatus.FAILED
    struc_check = next(c for c in dup_report.checks if c.check_id == "CHK-STRUC-01")
    assert struc_check.status == CheckStatus.FAILED
    assert "Duplicate file paths" in struc_check.message

    # 2. Unsafe path traversal
    unsafe_files = [
        GeneratedFile.model_construct(
            relative_path="../outside.py",
            content="print('evil')",
            purpose="Traversal attack",
        )
    ]
    unsafe_manifest = CodegenManifest.model_construct(
        project_name="Unsafe",
        archetype=sample_codegen_manifest.archetype,
        files=unsafe_files,
    )

    unsafe_report = validator.validate(unsafe_manifest, sample_analysis_result)
    assert unsafe_report.overall_status == CheckStatus.FAILED
    path_check = next(c for c in unsafe_report.checks if c.check_id == "CHK-PATH-02")
    assert path_check.status == CheckStatus.FAILED
    assert path_check.severity_if_failed == Severity.CRITICAL


def test_validate_python_syntax_errors(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)

    broken_files = [
        GeneratedFile(
            relative_path="requirements.txt",
            content="fastapi",
            purpose="deps",
        ),
        GeneratedFile(
            relative_path=".env.example",
            content="APP=test",
            purpose="env",
        ),
        GeneratedFile(
            relative_path="README.md",
            content="# Readme",
            purpose="docs",
        ),
        GeneratedFile(
            relative_path="app/broken.py",
            content="def syntax_error_func(:\n    return 42\n",  # SyntaxError
            purpose="Testing syntax error detection",
        ),
        GeneratedFile(
            relative_path="tests/test_app.py",
            content="def test_ok(): pass\n",
            purpose="tests",
        ),
    ]
    manifest = CodegenManifest(
        project_name="Syntax Test",
        archetype=sample_codegen_manifest.archetype,
        files=broken_files,
        completeness_notes="Syntax test notes",
    )

    report = validator.validate(manifest, sample_analysis_result)
    assert report.overall_status == CheckStatus.FAILED

    syntax_check = next(c for c in report.checks if c.check_id == "CHK-SYNTAX-03")
    assert syntax_check.status == CheckStatus.FAILED
    assert syntax_check.severity_if_failed == Severity.CRITICAL
    assert len(report.syntax_errors) >= 1
    assert "Syntax error in app/broken.py" in report.syntax_errors[0]


def test_validate_secrets_detection(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)

    leaked_files = [
        GeneratedFile(
            relative_path="requirements.txt",
            content="fastapi",
            purpose="deps",
        ),
        GeneratedFile(
            relative_path=".env.example",
            content="APP=test",
            purpose="env",
        ),
        GeneratedFile(
            relative_path="README.md",
            content="# Readme",
            purpose="docs",
        ),
        GeneratedFile(
            relative_path="app/config.py",
            content="GEMINI_API_KEY = 'AIzaSyD-LIVEKEY99887766554433221100'\n",
            purpose="Config with leaked secret",
        ),
        GeneratedFile(
            relative_path="tests/test_config.py",
            content="def test_dummy(): pass\n",
            purpose="tests",
        ),
    ]
    manifest = CodegenManifest(
        project_name="Secret Leak",
        archetype=sample_codegen_manifest.archetype,
        files=leaked_files,
        completeness_notes="Secret test notes",
    )

    report = validator.validate(manifest, sample_analysis_result)
    assert report.overall_status == CheckStatus.FAILED

    secrets_check = next(c for c in report.checks if c.check_id == "CHK-SECRETS-04")
    assert secrets_check.status == CheckStatus.FAILED
    assert secrets_check.severity_if_failed == Severity.CRITICAL
    assert "Potential live hardcoded secrets detected" in secrets_check.message


def test_validate_requirement_traceability(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)

    # Add an uncovered requirement to analysis
    analysis_with_uncovered = sample_analysis_result.model_copy(deep=True)
    analysis_with_uncovered.functional_requirements.append(
        Requirement(
            req_id="REQ-F-99",
            title="Biometric Quantum Teleportation",
            description="Teleport physical items via quantum mesh.",
            priority="low",
            category="functional",
            evidence=[],
        )
    )

    report = validator.validate(sample_codegen_manifest, analysis_with_uncovered)
    assert report.overall_status == CheckStatus.FAILED

    trace_check = next(c for c in report.checks if c.check_id == "CHK-TRACE-05")
    assert trace_check.status == CheckStatus.FAILED
    assert "uncovered requirements" in trace_check.message

    uncovered_link = next(l for l in report.traceability_matrix if l.req_id == "REQ-F-99")
    assert uncovered_link.status == "uncovered"


def test_correct_check_status_accounting(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)
    report = validator.validate(sample_codegen_manifest, sample_analysis_result)

    # Verify check status consistency
    assert report.checks_total == (
        report.checks_passed + report.checks_failed + report.checks_blocked + report.checks_not_run
    )
    # Check that test_execution is honestly marked NOT_RUN
    exec_check = next(c for c in report.checks if c.category == "test_execution")
    assert exec_check.status == CheckStatus.NOT_RUN
    assert "Dynamic execution skipped" in exec_check.message


def test_malformed_manifest_error_handling(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    validator = OutputValidator(settings=test_settings)

    # 1. Manifest is None
    report_none = validator.validate(None, sample_analysis_result)  # type: ignore
    assert report_none.overall_status == CheckStatus.FAILED
    assert report_none.checks_failed >= 1

    # 2. Manifest has empty files list
    empty_manifest = CodegenManifest.model_construct(
        project_name="Empty",
        archetype=sample_analysis_result.modules[0].name,  # type: ignore
        files=[],
    )
    report_empty = validator.validate(empty_manifest, sample_analysis_result)
    assert report_empty.overall_status == CheckStatus.FAILED


def test_offline_operation_without_gemini_api_key(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
):
    # Construct settings with completely empty dummy key and mock provider
    validator = OutputValidator(settings=None)
    report = validator.validate(sample_codegen_manifest, sample_analysis_result)

    assert report.overall_status == CheckStatus.PASSED
    assert report.checks_passed == 6
    assert report.checks_not_run == 1


def test_convenience_function_validate_generated_code(
    sample_codegen_manifest: CodegenManifest,
    sample_analysis_result: RequirementAnalysisResult,
):
    report = validate_generated_code(sample_codegen_manifest, sample_analysis_result)
    assert isinstance(report, ValidationReport)
    assert report.overall_status == CheckStatus.PASSED
