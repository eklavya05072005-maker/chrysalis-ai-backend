"""Module G: Output Validation Engine for Chrysalis AI.

Performs rigorous, bounded static validation of generated code artifacts,
including manifest structure, path safety, Python AST syntax, secret exposure,
requirement traceability, and documentation/test presence without executing untrusted code.
"""

from __future__ import annotations
import ast
import logging
import re
from typing import Any

from backend.app.ai.codegen_engine import SECRET_PATTERNS
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.architecture import ArchitectureCandidate
from backend.app.schemas.codegen import CodegenManifest, GeneratedFile
from backend.app.schemas.common import CheckStatus, Severity
from backend.app.schemas.validation import (
    TraceabilityLink,
    ValidationCheck,
    ValidationReport,
)

logger = logging.getLogger(__name__)


class OutputValidator:
    """Orchestrates deterministic static verification of generated project artifacts."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def validate_manifest_structure(self, manifest: CodegenManifest) -> tuple[ValidationCheck, list[str]]:
        """Verify manifest completeness, non-empty files, and absence of duplicate paths."""
        warnings: list[str] = []

        if manifest is None:
            return (
                ValidationCheck(
                    check_id="CHK-STRUC-01",
                    name="Manifest Completeness",
                    category="file_structure",
                    status=CheckStatus.FAILED,
                    severity_if_failed=Severity.CRITICAL,
                    message="CodegenManifest is None.",
                ),
                ["CodegenManifest is None"],
            )

        if not manifest.files:
            return (
                ValidationCheck(
                    check_id="CHK-STRUC-01",
                    name="Manifest Completeness",
                    category="file_structure",
                    status=CheckStatus.FAILED,
                    severity_if_failed=Severity.CRITICAL,
                    message="Manifest contains zero generated files.",
                ),
                ["Manifest contains zero generated files"],
            )

        # Check for duplicate paths
        seen_paths: set[str] = set()
        duplicate_paths: list[str] = []
        for f in manifest.files:
            norm = f.relative_path.replace("\\", "/").strip().lower()
            if norm in seen_paths:
                duplicate_paths.append(f.relative_path)
            seen_paths.add(norm)

        if duplicate_paths:
            return (
                ValidationCheck(
                    check_id="CHK-STRUC-01",
                    name="Manifest Completeness",
                    category="file_structure",
                    status=CheckStatus.FAILED,
                    severity_if_failed=Severity.HIGH,
                    message=f"Duplicate file paths detected in manifest: {', '.join(duplicate_paths)}",
                    details={"duplicates": duplicate_paths},
                ),
                [f"Duplicate path: {p}" for p in duplicate_paths],
            )

        # Check for empty files
        empty_files = [f.relative_path for f in manifest.files if not f.content or not f.content.strip()]
        if empty_files:
            return (
                ValidationCheck(
                    check_id="CHK-STRUC-01",
                    name="Manifest Completeness",
                    category="field_completeness",
                    status=CheckStatus.FAILED,
                    severity_if_failed=Severity.HIGH,
                    message=f"Empty content detected in files: {', '.join(empty_files)}",
                    details={"empty_files": empty_files},
                ),
                [f"Empty file: {p}" for p in empty_files],
            )

        # Check core files presence
        all_paths = {f.relative_path.replace("\\", "/").strip() for f in manifest.files}
        missing_core: list[str] = []
        if "requirements.txt" not in all_paths:
            missing_core.append("requirements.txt")
        if ".env.example" not in all_paths:
            missing_core.append(".env.example")
        if "README.md" not in all_paths:
            missing_core.append("README.md")

        if missing_core:
            return (
                ValidationCheck(
                    check_id="CHK-STRUC-01",
                    name="Manifest Completeness",
                    category="file_structure",
                    status=CheckStatus.FAILED,
                    severity_if_failed=Severity.HIGH,
                    message=f"Essential project configuration files missing: {', '.join(missing_core)}",
                    details={"missing_core_files": missing_core},
                ),
                [f"Missing core file: {f}" for f in missing_core],
            )

        return (
            ValidationCheck(
                check_id="CHK-STRUC-01",
                name="Manifest Completeness",
                category="file_structure",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.HIGH,
                message=f"Manifest structure verified with {len(manifest.files)} valid unique files.",
                details={"total_files": len(manifest.files)},
            ),
            [],
        )

    def validate_paths_safety(self, manifest: CodegenManifest) -> ValidationCheck:
        """Enforce path-traversal defense and safe relative containment."""
        if not manifest or not manifest.files:
            return ValidationCheck(
                check_id="CHK-PATH-02",
                name="Path Safety & Traversal Defense",
                category="schema_validation",
                status=CheckStatus.BLOCKED,
                severity_if_failed=Severity.CRITICAL,
                message="Path safety check blocked due to missing manifest files.",
            )

        unsafe_paths: list[str] = []
        for f in manifest.files:
            norm = f.relative_path.replace("\\", "/").strip()
            if (
                ":" in norm
                or norm.startswith("/")
                or norm.startswith("../")
                or "/../" in norm
                or norm == ".."
                or norm.startswith("\\")
            ):
                unsafe_paths.append(f.relative_path)

        if unsafe_paths:
            return ValidationCheck(
                check_id="CHK-PATH-02",
                name="Path Safety & Traversal Defense",
                category="schema_validation",
                status=CheckStatus.FAILED,
                severity_if_failed=Severity.CRITICAL,
                message=f"Dangerous path traversal or absolute paths detected: {', '.join(unsafe_paths)}",
                details={"unsafe_paths": unsafe_paths},
            )

        return ValidationCheck(
            check_id="CHK-PATH-02",
            name="Path Safety & Traversal Defense",
            category="schema_validation",
            status=CheckStatus.PASSED,
            severity_if_failed=Severity.CRITICAL,
            message="All file paths strictly conform to safe relative path boundaries.",
        )

    def validate_python_syntax(self, manifest: CodegenManifest) -> tuple[ValidationCheck, list[str]]:
        """Statically parse Python files with AST without executing untrusted code."""
        if not manifest or not manifest.files:
            return (
                ValidationCheck(
                    check_id="CHK-SYNTAX-03",
                    name="Python AST Syntax Check",
                    category="syntax_check",
                    status=CheckStatus.BLOCKED,
                    severity_if_failed=Severity.CRITICAL,
                    message="Syntax check blocked: no manifest files provided.",
                ),
                [],
            )

        python_files = [f for f in manifest.files if f.relative_path.endswith(".py")]
        syntax_errors: list[str] = []

        for pf in python_files:
            try:
                ast.parse(pf.content, filename=pf.relative_path)
            except SyntaxError as err:
                msg = f"Syntax error in {pf.relative_path}:{err.lineno}:{err.offset} - {err.msg}"
                syntax_errors.append(msg)
            except Exception as err:
                msg = f"Failed to parse {pf.relative_path}: {err}"
                syntax_errors.append(msg)

        if syntax_errors:
            return (
                ValidationCheck(
                    check_id="CHK-SYNTAX-03",
                    name="Python AST Syntax Check",
                    category="syntax_check",
                    status=CheckStatus.FAILED,
                    severity_if_failed=Severity.CRITICAL,
                    message=f"Python AST parser discovered {len(syntax_errors)} syntax errors.",
                    details={"syntax_errors": syntax_errors},
                ),
                syntax_errors,
            )

        return (
            ValidationCheck(
                check_id="CHK-SYNTAX-03",
                name="Python AST Syntax Check",
                category="syntax_check",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.CRITICAL,
                message=f"All {len(python_files)} Python source files parsed cleanly with zero AST syntax errors.",
                details={"verified_python_files_count": len(python_files)},
            ),
            [],
        )

    def validate_secrets(self, manifest: CodegenManifest) -> ValidationCheck:
        """Scan generated source files for hardcoded live API keys or credentials."""
        if not manifest or not manifest.files:
            return ValidationCheck(
                check_id="CHK-SECRETS-04",
                name="Secrets & Credentials Audit",
                category="schema_validation",
                status=CheckStatus.BLOCKED,
                severity_if_failed=Severity.CRITICAL,
                message="Secrets scan blocked: no manifest files provided.",
            )

        compromised_files: list[str] = []

        for f in manifest.files:
            if f.relative_path.endswith(".env.example"):
                continue

            for pattern in SECRET_PATTERNS:
                match = pattern.search(f.content)
                if match:
                    matched_str = match.group(0).lower()
                    if not any(ph in matched_str for ph in ["your-", "dummy", "placeholder", "xxx", "example"]):
                        compromised_files.append(f.relative_path)
                        break

        if compromised_files:
            return ValidationCheck(
                check_id="CHK-SECRETS-04",
                name="Secrets & Credentials Audit",
                category="schema_validation",
                status=CheckStatus.FAILED,
                severity_if_failed=Severity.CRITICAL,
                message=f"Potential live hardcoded secrets detected in files: {', '.join(compromised_files)}",
                details={"compromised_files": compromised_files},
            )

        return ValidationCheck(
            check_id="CHK-SECRETS-04",
            name="Secrets & Credentials Audit",
            category="schema_validation",
            status=CheckStatus.PASSED,
            severity_if_failed=Severity.CRITICAL,
            message="Zero hardcoded credentials or API tokens detected across generated files.",
        )

    def validate_traceability(
        self,
        manifest: CodegenManifest,
        analysis: RequirementAnalysisResult,
    ) -> tuple[ValidationCheck, list[TraceabilityLink]]:
        """Map requirements and business rules to generated source files."""
        if not manifest or not manifest.files or not analysis:
            return (
                ValidationCheck(
                    check_id="CHK-TRACE-05",
                    name="Requirement & Rule Traceability",
                    category="traceability",
                    status=CheckStatus.BLOCKED,
                    severity_if_failed=Severity.HIGH,
                    message="Traceability check blocked: missing manifest or requirement analysis.",
                ),
                [],
            )

        all_content_combined = "\n".join([f.content for f in manifest.files]).lower()
        file_content_map = {f.relative_path: f.content.lower() for f in manifest.files}

        trace_matrix: list[TraceabilityLink] = []
        uncovered_items: list[str] = []

        # Trace functional requirements
        for req in analysis.functional_requirements:
            mapped_files: list[str] = []
            req_id_lower = req.req_id.lower()
            title_keywords = [w.lower() for w in req.title.split() if len(w) > 3]

            for path, content in file_content_map.items():
                if req_id_lower in content or any(kw in content for kw in title_keywords):
                    mapped_files.append(path)

            if mapped_files:
                trace_matrix.append(
                    TraceabilityLink(
                        req_id=req.req_id,
                        req_title=req.title,
                        mapped_component_ids=mapped_files,
                        status="covered",
                        notes=f"Implemented across: {', '.join(mapped_files)}",
                    )
                )
            else:
                uncovered_items.append(req.req_id)
                trace_matrix.append(
                    TraceabilityLink(
                        req_id=req.req_id,
                        req_title=req.title,
                        mapped_component_ids=[],
                        status="uncovered",
                        notes="No explicit keyword or ID reference found in generated code.",
                    )
                )

        # Trace business rules
        for rule in analysis.business_rules:
            mapped_files = []
            rule_id_lower = rule.rule_id.lower()
            rule_keywords = [w.lower() for w in rule.description.split() if len(w) > 4]

            # Look for rule ID or numerical thresholds (e.g. 10000)
            threshold_match = re.search(r"\d{3,}", rule.description)
            threshold_str = threshold_match.group(0) if threshold_match else ""

            for path, content in file_content_map.items():
                if (
                    rule_id_lower in content
                    or (threshold_str and threshold_str in content)
                    or any(kw in content for kw in rule_keywords[:2])
                ):
                    mapped_files.append(path)

            if mapped_files:
                trace_matrix.append(
                    TraceabilityLink(
                        req_id=rule.rule_id,
                        req_title=rule.description[:60],
                        mapped_component_ids=mapped_files,
                        status="covered",
                        notes=f"Business rule enforced in: {', '.join(mapped_files)}",
                    )
                )
            else:
                uncovered_items.append(rule.rule_id)
                trace_matrix.append(
                    TraceabilityLink(
                        req_id=rule.rule_id,
                        req_title=rule.description[:60],
                        mapped_component_ids=[],
                        status="uncovered",
                        notes="No explicit threshold or rule reference discovered.",
                    )
                )

        if uncovered_items:
            return (
                ValidationCheck(
                    check_id="CHK-TRACE-05",
                    name="Requirement & Rule Traceability",
                    category="traceability",
                    status=CheckStatus.FAILED,
                    severity_if_failed=Severity.HIGH,
                    message=f"Traceability check discovered {len(uncovered_items)} uncovered requirements/rules: {', '.join(uncovered_items)}",
                    details={"uncovered_items": uncovered_items},
                ),
                trace_matrix,
            )

        return (
            ValidationCheck(
                check_id="CHK-TRACE-05",
                name="Requirement & Rule Traceability",
                category="traceability",
                status=CheckStatus.PASSED,
                severity_if_failed=Severity.HIGH,
                message=f"All {len(trace_matrix)} functional requirements and business rules are mapped to source files.",
                details={"total_traced_items": len(trace_matrix)},
            ),
            trace_matrix,
        )

    def validate_documentation_and_tests(self, manifest: CodegenManifest) -> ValidationCheck:
        """Verify presence of unit test suite and setup documentation."""
        if not manifest or not manifest.files:
            return ValidationCheck(
                check_id="CHK-TESTS-06",
                name="Documentation & Test Suite Presence",
                category="field_completeness",
                status=CheckStatus.BLOCKED,
                severity_if_failed=Severity.HIGH,
                message="Documentation and test verification blocked: no manifest files.",
            )

        has_readme = any(f.relative_path.lower() in ["readme.md", "readme.txt"] for f in manifest.files)
        has_tests = any(
            f.relative_path.startswith("tests/") or "test_" in f.relative_path.lower()
            for f in manifest.files
        )

        if not has_readme and not has_tests:
            return ValidationCheck(
                check_id="CHK-TESTS-06",
                name="Documentation & Test Suite Presence",
                category="field_completeness",
                status=CheckStatus.FAILED,
                severity_if_failed=Severity.HIGH,
                message="Both project documentation (README.md) and unit test files are missing.",
            )
        elif not has_readme:
            return ValidationCheck(
                check_id="CHK-TESTS-06",
                name="Documentation & Test Suite Presence",
                category="field_completeness",
                status=CheckStatus.FAILED,
                severity_if_failed=Severity.WARNING,
                message="Project README.md documentation is missing.",
            )
        elif not has_tests:
            return ValidationCheck(
                check_id="CHK-TESTS-06",
                name="Documentation & Test Suite Presence",
                category="field_completeness",
                status=CheckStatus.FAILED,
                severity_if_failed=Severity.HIGH,
                message="No unit test suite discovered (expected tests/ directory or test_*.py).",
            )

        return ValidationCheck(
            check_id="CHK-TESTS-06",
            name="Documentation & Test Suite Presence",
            category="field_completeness",
            status=CheckStatus.PASSED,
            severity_if_failed=Severity.HIGH,
            message="Both README.md setup documentation and unit test suite are present.",
        )

    def validate(
        self,
        manifest: CodegenManifest,
        analysis: RequirementAnalysisResult,
        candidate_id: str | None = None,
        candidate: ArchitectureCandidate | None = None,
    ) -> ValidationReport:
        """Execute complete bounded static validation pipeline and return honest ValidationReport."""
        target_cand_id = candidate_id or (candidate.candidate_id if candidate else "CAND-SELECTED")
        target_proj_name = (
            manifest.project_name
            if manifest and manifest.project_name
            else (analysis.project_name if analysis else "Unknown Project")
        )

        all_checks: list[ValidationCheck] = []
        all_warnings: list[str] = []
        all_syntax_errors: list[str] = []
        trace_matrix: list[TraceabilityLink] = []

        # 1. Manifest structure check
        struc_check, struc_warnings = self.validate_manifest_structure(manifest)
        all_checks.append(struc_check)
        all_warnings.extend(struc_warnings)

        # 2. Path safety check
        path_check = self.validate_paths_safety(manifest)
        all_checks.append(path_check)

        # 3. Python AST syntax check
        syntax_check, syntax_errs = self.validate_python_syntax(manifest)
        all_checks.append(syntax_check)
        all_syntax_errors.extend(syntax_errs)

        # 4. Secrets audit check
        secrets_check = self.validate_secrets(manifest)
        all_checks.append(secrets_check)

        # 5. Requirement traceability check
        trace_check, matrix = self.validate_traceability(manifest, analysis)
        all_checks.append(trace_check)
        trace_matrix.extend(matrix)

        # 6. Documentation and test presence check
        docs_check = self.validate_documentation_and_tests(manifest)
        all_checks.append(docs_check)

        # 7. Dynamic execution check (honest not_run record)
        exec_check = ValidationCheck(
            check_id="CHK-EXEC-07",
            name="Dynamic Test Execution",
            category="test_execution",
            status=CheckStatus.NOT_RUN,
            severity_if_failed=Severity.INFO,
            message="Dynamic execution skipped. Chrysalis AI treats generated source code as untrusted input and performs bounded static validation only.",
        )
        all_checks.append(exec_check)

        # Calculate counts
        passed_count = sum(1 for c in all_checks if c.status == CheckStatus.PASSED)
        failed_count = sum(1 for c in all_checks if c.status == CheckStatus.FAILED)
        blocked_count = sum(1 for c in all_checks if c.status == CheckStatus.BLOCKED)
        not_run_count = sum(1 for c in all_checks if c.status == CheckStatus.NOT_RUN)

        if failed_count > 0:
            overall = CheckStatus.FAILED
        elif blocked_count > 0:
            overall = CheckStatus.BLOCKED
        elif passed_count > 0:
            overall = CheckStatus.PASSED
        else:
            overall = CheckStatus.NOT_RUN

        return ValidationReport(
            project_name=target_proj_name,
            candidate_id=target_cand_id,
            overall_status=overall,
            checks_total=len(all_checks),
            checks_passed=passed_count,
            checks_failed=failed_count,
            checks_blocked=blocked_count,
            checks_not_run=not_run_count,
            checks=all_checks,
            traceability_matrix=trace_matrix,
            syntax_errors=all_syntax_errors,
            warnings=all_warnings,
        )


def validate_generated_code(
    manifest: CodegenManifest,
    analysis: RequirementAnalysisResult,
    candidate_id: str | None = None,
    candidate: ArchitectureCandidate | None = None,
    settings: Settings | None = None,
) -> ValidationReport:
    """Convenience helper to run bounded static validation over generated artifacts."""
    validator = OutputValidator(settings=settings)
    return validator.validate(
        manifest=manifest,
        analysis=analysis,
        candidate_id=candidate_id,
        candidate=candidate,
    )
