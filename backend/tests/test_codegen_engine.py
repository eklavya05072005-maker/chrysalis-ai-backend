"""Unit tests for Module F: Code Generation Engine.

All tests run offline using MockLLMClient and fixtures without external API calls.
"""

from pathlib import Path
import pytest
from backend.app.ai.codegen_engine import (
    CodegenEngine,
    generate_project_code,
    validate_safe_output_path,
    verify_no_secrets,
    write_manifest_to_disk,
)
from backend.app.core.config import Settings
from backend.app.integrations.llm_client import (
    LLMAuthenticationError,
    LLMError,
    LLMMalformedJSONError,
    LLMTimeoutError,
    MockLLMClient,
)
from backend.app.schemas import (
    ArchitectureCandidatesResult,
    CodegenManifest,
    GeneratedFile,
    RequirementAnalysisResult,
    TaskClassificationResult,
)


@pytest.mark.asyncio
async def test_generate_manifest_offline(
    mock_llm_client: MockLLMClient,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    sample_classification_result: TaskClassificationResult,
    test_settings: Settings,
):
    selected_candidate = sample_architecture_candidates_result.candidates[0]
    engine = CodegenEngine(llm_client=mock_llm_client, settings=test_settings)

    manifest = await engine.generate_manifest(
        selected_candidate=selected_candidate,
        analysis=sample_analysis_result,
        classification=sample_classification_result,
    )

    assert isinstance(manifest, CodegenManifest)
    assert manifest.total_files >= 5
    assert len(manifest.files) >= 5

    file_paths = {f.relative_path for f in manifest.files}
    assert "requirements.txt" in file_paths
    assert ".env.example" in file_paths
    assert "app/main.py" in file_paths
    assert "app/schemas.py" in file_paths
    assert "app/services.py" in file_paths
    assert "tests/test_app.py" in file_paths
    assert "README.md" in file_paths

    assert len(manifest.setup_instructions) >= 3
    assert len(manifest.completeness_notes) > 10
    assert manifest.is_fully_generated is True


@pytest.mark.asyncio
async def test_requirement_traceability_in_generated_files(
    mock_llm_client: MockLLMClient,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    selected_candidate = sample_architecture_candidates_result.candidates[0]
    engine = CodegenEngine(llm_client=mock_llm_client, settings=test_settings)

    manifest = await engine.generate_manifest(
        selected_candidate=selected_candidate,
        analysis=sample_analysis_result,
    )

    # Check that Rule BR-01 ($10,000 threshold or manager approval) is implemented in services.py
    services_file = next(f for f in manifest.files if f.relative_path == "app/services.py")
    assert "10000" in services_file.content or "approval" in services_file.content.lower()

    # Check tests verify Rule BR-01
    test_file = next(f for f in manifest.files if f.relative_path == "tests/test_app.py")
    assert "approval" in test_file.content.lower()


@pytest.mark.asyncio
async def test_write_manifest_to_disk_creates_actual_files(
    mock_llm_client: MockLLMClient,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
    tmp_path: Path,
):
    selected_candidate = sample_architecture_candidates_result.candidates[0]
    engine = CodegenEngine(llm_client=mock_llm_client, settings=test_settings)

    output_dir = tmp_path / "test_generated_project"
    manifest, created_paths = await engine.generate_and_write(
        selected_candidate=selected_candidate,
        analysis=sample_analysis_result,
        output_dir=output_dir,
    )

    assert output_dir.exists()
    assert len(created_paths) == len(manifest.files)

    for gen_file in manifest.files:
        disk_path = output_dir / gen_file.relative_path
        assert disk_path.exists()
        assert disk_path.is_file()
        assert disk_path.read_text(encoding="utf-8") == gen_file.content


def test_safe_path_validation_and_traversal_attacks(tmp_path: Path):
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()

    # Valid safe path
    safe_path = validate_safe_output_path(base_dir, "app/routers/invoices.py")
    assert safe_path == (base_dir / "app/routers/invoices.py").resolve()

    # Directory traversal prefix
    with pytest.raises(ValueError) as exc1:
        validate_safe_output_path(base_dir, "../escape.py")
    assert "Dangerous path traversal" in str(exc1.value)

    # Internal directory traversal
    with pytest.raises(ValueError) as exc2:
        validate_safe_output_path(base_dir, "app/../../outside.py")
    assert "Dangerous path traversal" in str(exc2.value)

    # Absolute unix path
    with pytest.raises(ValueError) as exc3:
        validate_safe_output_path(base_dir, "/etc/passwd")
    assert "Absolute unix path" in str(exc3.value)

    # Windows drive path
    with pytest.raises(ValueError) as exc4:
        validate_safe_output_path(base_dir, "C:/Windows/System32/evil.dll")
    assert "drive letter" in str(exc4.value)

    # Empty path
    with pytest.raises(ValueError) as exc5:
        validate_safe_output_path(base_dir, "")
    assert "cannot be empty" in str(exc5.value)


def test_existing_destination_overwrite_protection(
    sample_codegen_manifest: CodegenManifest,
    tmp_path: Path,
):
    existing_dir = tmp_path / "user_existing_project"
    existing_dir.mkdir()
    (existing_dir / "user_precious_file.txt").write_text("DO NOT OVERWRITE", encoding="utf-8")

    # Attempt write without overwrite=True must fail
    with pytest.raises(FileExistsError) as exc:
        write_manifest_to_disk(sample_codegen_manifest, output_dir=existing_dir, overwrite=False)
    assert "already exists and contains files" in str(exc.value)

    # user file is untouched
    assert (existing_dir / "user_precious_file.txt").read_text(encoding="utf-8") == "DO NOT OVERWRITE"

    # With overwrite=True, write succeeds
    created = write_manifest_to_disk(sample_codegen_manifest, output_dir=existing_dir, overwrite=True)
    assert len(created) == len(sample_codegen_manifest.files)


def test_secrets_protection():
    # Clean code passes
    verify_no_secrets("API_KEY = os.getenv('API_KEY')", "app/config.py")

    # .env.example with placeholders passes
    verify_no_secrets("API_KEY=your-api-key-here", ".env.example")

    # Live Google API key is rejected
    with pytest.raises(ValueError) as exc1:
        verify_no_secrets("API_KEY = 'AIzaSyD-TESTKEY99887766554433221100'", "app/config.py")
    assert "Suspected hardcoded secret detected" in str(exc1.value)

    # Live OpenAI API key is rejected
    with pytest.raises(ValueError) as exc2:
        verify_no_secrets("openai_key = 'sk-1234567890abcdef1234567890abcdef12'", "app/config.py")
    assert "Suspected hardcoded secret detected" in str(exc2.value)


def test_empty_or_insufficient_input_raises_value_error(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = CodegenEngine(llm_client=MockLLMClient(), settings=test_settings)
    cand = sample_architecture_candidates_result.candidates[0]

    # None candidate
    with pytest.raises(ValueError) as exc1:
        engine.validate_inputs(None, sample_analysis_result)  # type: ignore
    assert "Selected architecture candidate must be provided" in str(exc1.value)

    # None analysis
    with pytest.raises(ValueError) as exc2:
        engine.validate_inputs(cand, None)  # type: ignore
    assert "Requirement analysis must be provided" in str(exc2.value)

    # Empty analysis
    empty_analysis = RequirementAnalysisResult(
        project_name="Empty",
        executive_summary="Empty",
        modules=[],
        workflows=[],
        business_rules=[],
        functional_requirements=[],
        non_functional_requirements=[],
        risks_and_ambiguities=[],
        evidence_references=[],
    )
    with pytest.raises(ValueError) as exc3:
        engine.validate_inputs(cand, empty_analysis)
    assert "must contain requirements or business rules" in str(exc3.value)


def test_empty_files_manifest_from_llm_raises_error(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = CodegenEngine(llm_client=MockLLMClient(), settings=test_settings)
    cand = sample_architecture_candidates_result.candidates[0]
    empty_manifest = CodegenManifest.model_construct(
        project_name=sample_analysis_result.project_name,
        archetype=cand.archetype,
        files=[],
    )

    with pytest.raises(LLMError) as exc:
        engine._verify_and_sanitize_manifest(empty_manifest, cand, sample_analysis_result)
    assert "empty file manifest" in str(exc.value)


@pytest.mark.asyncio
async def test_timeout_propagated(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_timeout(True)

    engine = CodegenEngine(llm_client=mock_client, settings=test_settings)
    cand = sample_architecture_candidates_result.candidates[0]
    with pytest.raises(LLMTimeoutError):
        await engine.generate_manifest(cand, sample_analysis_result)


@pytest.mark.asyncio
async def test_provider_failure_propagated(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_auth_failure(True)

    engine = CodegenEngine(llm_client=mock_client, settings=test_settings)
    cand = sample_architecture_candidates_result.candidates[0]
    with pytest.raises(LLMAuthenticationError):
        await engine.generate_manifest(cand, sample_analysis_result)


@pytest.mark.asyncio
async def test_malformed_llm_json_propagated(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_malformed_json(True)

    engine = CodegenEngine(llm_client=mock_client, settings=test_settings)
    cand = sample_architecture_candidates_result.candidates[0]
    with pytest.raises(LLMMalformedJSONError):
        await engine.generate_manifest(cand, sample_analysis_result)


@pytest.mark.asyncio
async def test_convenience_function_generate_project_code(
    mock_llm_client: MockLLMClient,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    tmp_path: Path,
):
    cand = sample_architecture_candidates_result.candidates[0]
    output_dir = tmp_path / "convenience_proj"

    manifest, written_paths = await generate_project_code(
        selected_candidate=cand,
        analysis=sample_analysis_result,
        output_dir=output_dir,
        llm_client=mock_llm_client,
    )

    assert isinstance(manifest, CodegenManifest)
    assert written_paths is not None
    assert len(written_paths) == len(manifest.files)
    assert output_dir.exists()
