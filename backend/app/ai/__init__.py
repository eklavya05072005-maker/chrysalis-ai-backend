"""AI module package for Chrysalis AI analysis, classification, and architecture reasoning."""

from backend.app.ai.analyzer import RequirementAnalyzer, analyze_requirements
from backend.app.ai.architecture_generator import (
    ArchitectureSearchEngine,
    generate_architecture_candidates,
)
from backend.app.ai.classifier import TaskClassifier, classify_tasks
from backend.app.ai.codegen_engine import (
    CodegenEngine,
    generate_project_code,
    validate_safe_output_path,
    write_manifest_to_disk,
)
from backend.app.ai.evaluator import (
    ArchitectureEvaluator,
    evaluate_architecture_candidates,
)
from backend.app.ai.scenario_designer import (
    ScenarioDesignEngine,
    design_benchmark_scenarios,
)
from backend.app.ai.validator import (
    OutputValidator,
    validate_generated_code,
)

__all__ = [
    "RequirementAnalyzer",
    "analyze_requirements",
    "TaskClassifier",
    "classify_tasks",
    "ArchitectureSearchEngine",
    "generate_architecture_candidates",
    "ArchitectureEvaluator",
    "evaluate_architecture_candidates",
    "ScenarioDesignEngine",
    "design_benchmark_scenarios",
    "CodegenEngine",
    "generate_project_code",
    "validate_safe_output_path",
    "write_manifest_to_disk",
    "OutputValidator",
    "validate_generated_code",
]
