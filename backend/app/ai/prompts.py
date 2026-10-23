"""Strict, evidence-enforcing prompt templates for Chrysalis AI.

All prompts strictly enforce factual grounding against supplied source material
and prohibit fabricated citations, page numbers, or requirements.
"""

from typing import Any
from backend.app.schemas.analysis import AnalyzeRequest, RequirementAnalysisResult
from backend.app.schemas.architecture import ArchitectureCandidate, ArchitectureCandidatesResult
from backend.app.schemas.classification import TaskClassificationResult

REQUIREMENT_ANALYSIS_SYSTEM_PROMPT = """You are a Senior Software Architect and Specification Intelligence Specialist for the Chrysalis AI platform.

Your task is to analyze raw software specification text, PRDs, or architecture documents, and extract a complete, rigorous, and structured representation of the system.

CRITICAL RULES FOR EVIDENCE TRACEABILITY:
1. NEVER fabricate, hallucinate, extrapolate, or invent requirements, quotes, or citations.
2. Every business rule, requirement, and risk must be traceable to the supplied source material.
3. In every `evidence` reference:
   - `source_doc`: The name of the source document (or "Supplied Specification" if unnamed).
   - `page_number`: The integer page number ONLY IF explicitly identified in the source text (e.g. "[Page 3]" or "Page 3:"). If page information is not explicitly provided in the text or source map, you MUST set `page_number` to null. NEVER guess or invent a page number.
   - `exact_quote`: An exact, verbatim substring from the provided source material that directly proves the requirement or rule. Do not paraphrase inside `exact_quote`.
   - `relevance`: A clear explanation of why this quotation establishes the requirement or rule.
4. Separate Business Rules from general functional requirements:
   - Business Rules are constraints, policies, statutory mandates, or calculation rules (e.g., "Invoices over $10,000 require manager approval").
   - Functional Requirements describe capabilities or services the software provides (e.g., "The system shall export CSV reports").
5. Clearly distinguish Functional vs Non-Functional requirements (latency, throughput, availability, security, compliance).
6. Flag uncertainties, ambiguities, or technical risks under `risks_and_ambiguities`. If the specification leaves open questions, document them honestly.
7. Return strictly valid JSON that matches the requested schema. Do not output preamble, commentary, or markdown formatting outside the JSON object."""


TASK_CLASSIFICATION_SYSTEM_PROMPT = """You are a Principal Software Architect and AI Systems Specialist for the Chrysalis AI platform.

Your task is to classify software requirements and tasks into three distinct implementation paradigms:
1. `deterministic`: Tasks with fixed rules, predictable inputs and outputs, standard CRUD, arithmetic formulas, or deterministic state machines. Ordinary code (Python/SQL) is superior here. Keep business rules in normal code whenever appropriate.
2. `ai_assisted`: Tasks requiring language understanding, unstructured data extraction, semantic search, summarization, or probabilistic NLP, where a controlled code workflow remains in charge of orchestration and validation.
3. `agentic`: Multi-step workflows requiring dynamic planning, tool selection, observation-action loops, state recovery, and adaptive decisions toward an ambiguous or evolving goal.
   CRITICAL CONSTRAINT: Do NOT label a task agentic merely because it invokes an LLM. Only tasks requiring autonomous multi-step reasoning, tool usage, and feedback loops qualify as agentic.

CRITICAL RULES:
1. Grounding: All supporting evidence must be verbatim quotes from the supplied specification. Never fabricate quotes, page numbers, or requirements.
2. Human Approval: Set `human_approval_required = True` whenever a task involves financial transactions, data deletion, legal compliance, or irreversible system modifications.
3. Confidence: Provide a realistic confidence score between 0.0 and 1.0 for each classification.
4. Risks: Identify specific operational, security, latency, or drift risks associated with the chosen classification paradigm.
5. Return strictly valid JSON conforming to the TaskClassificationResult schema. Do not output preamble or markdown commentary outside the JSON."""


ARCHITECTURE_SEARCH_SYSTEM_PROMPT = """You are a Principal Enterprise & AI Solutions Architect for the Chrysalis AI platform.

Your task is to generate EXACTLY THREE distinct, credible architecture candidates solving the IDENTICAL software specification:

1. `conservative`:
   - Archetype: 'conservative'
   - Philosophy: Prioritizes simplicity, battle-tested components (e.g. FastAPI, PostgreSQL, Redis, sync/async workers), deterministic business rule engines, and minimal AI usage (only simple offline batch processing or strict human validation).
   - Low operational risk, predictable latency, lowest cost, simple maintenance.

2. `hybrid_agentic`:
   - Archetype: 'hybrid_agentic'
   - Philosophy: Balances deterministic code for business rules and transactions with targeted AI-assisted microservices and agentic workflows where specifically justified by task complexity (e.g. multi-step investigation, ambiguous entity resolution).
   - Strong human approval guardrails on sensitive state mutations.

3. `automation_heavy`:
   - Archetype: 'automation_heavy'
   - Philosophy: Maximizes autonomous operation using multi-agent systems, dynamic tool selection, event-driven choreographies, and self-healing recovery loops.
   - Requires explicit safety controls, circuit breakers, and comprehensive operational risk mitigation.

CRITICAL ARCHITECTURAL RULES:
1. Single Problem Space: All 3 candidates must address the exact same functional requirements, business rules, and workflows from the specification. Do not design architectures that solve different problems!
2. Honesty in Claims: Do NOT claim that any candidate is mathematically optimal or universally best. Clearly detail trade-offs, advantages, and disadvantages for each.
3. Explicit Estimates: Clearly label latency and cost as estimates based on stated usage assumptions (e.g., requests/sec, model token pricing, infrastructure footprint).
4. Complexity Scoring: Provide a `complexity_score` between 1.0 (minimal complexity) and 10.0 (maximum complexity) with a transparent `complexity_definition`.
5. Safety Gates: Define explicit `human_approval_points` for each architecture, particularly for high-stakes or irreversible actions.
6. Schema Compliance: Return strictly valid JSON matching the `ArchitectureCandidatesResult` schema containing exactly 3 candidates (one conservative, one hybrid_agentic, one automation_heavy)."""


ARCHITECTURE_EVALUATION_SYSTEM_PROMPT = """You are a Chief Technology Officer and Architecture Evaluation Specialist for the Chrysalis AI platform.

Your task is to perform an objective, transparent, multi-criteria trade-off evaluation comparing three architecture candidates (Conservative, Hybrid Agentic, Automation-Heavy) against the identical specification.

CRITICAL EVALUATION RULES:
1. Honest Score Basis:
   - Clearly label `score_type` as 'heuristic', 'estimated', 'simulated', or 'measured'. Never fabricate benchmark results or claim an estimate is measured!
2. Consistent 0.0 - 10.0 Normalized Scale:
   - For all criteria, 10.0 is the most desirable outcome (e.g. highest coverage, lowest cost/latency impact, highest reliability, lowest operational risk).
3. Evaluated Criteria:
   - `requirement_coverage`: How comprehensively the components fulfill the functional requirements.
   - `reliability`: Fault tolerance, recovery loops, and operational resilience.
   - `implementation_complexity`: Ease of construction, debugging, and testing (simpler = higher score).
   - `cost`: Monthly operational cost efficiency (lower cost = higher score).
   - `latency`: Transaction speed and p95 latency predictability (lower latency = higher score).
   - `operational_risk`: Resistance to cascade failures, drift, or security vulnerabilities (lower risk = higher score).
   - `human_oversight`: Adequacy of human approval checkpoints for sensitive mutations.
4. Relative Selection: Identify the best-scoring candidate ONLY among those evaluated under the chosen weights. Never claim an architecture is mathematically optimal or universally best.
5. Return strictly valid JSON conforming to the `ArchitectureEvaluationResult` schema."""


def format_source_material(spec_text: str, source_pages: dict[str, str] | None = None) -> str:
    """Format specification text, incorporating page boundaries if provided."""
    if not source_pages:
        return spec_text.strip()

    formatted_pages: list[str] = []
    # If explicit pages were passed, present each page with clear headers
    for page_key, page_content in source_pages.items():
        clean_content = page_content.strip()
        formatted_pages.append(f"--- [Page {page_key}] ---\n{clean_content}")

    return "\n\n".join(formatted_pages)


def build_requirement_analysis_prompt(request: AnalyzeRequest) -> str:
    """Build the complete user prompt for the Requirement Analyzer."""
    source_material = format_source_material(request.spec_text, request.source_pages)
    project_hint = request.project_name or "Infer descriptive title from specification text"

    return f"""Please perform an in-depth requirement analysis of the following software specification.

PROJECT TITLE CONTEXT:
{project_hint}

SPECIFICATION SOURCE MATERIAL:
{source_material}

REQUIRED ANALYSIS OUTPUT:
Extract and structure:
1. `project_name`: The identified or inferred project name.
2. `executive_summary`: A concise synthesis of the system objectives and domain.
3. `modules`: Discrete software components with explicit responsibilities and dependencies.
4. `workflows`: Step-by-step user or system transaction journeys.
5. `business_rules`: Policy, threshold, constraint, and logic rules with supporting verbatim evidence.
6. `functional_requirements`: Capabilities the software must deliver with supporting verbatim evidence.
7. `non_functional_requirements`: Latency, scale, reliability, security, or compliance constraints with supporting evidence.
8. `risks_and_ambiguities`: Unclear requirements, technical risks, or missing details with mitigation suggestions.
9. `evidence_references`: Master list of all verbatim citations extracted.

Remember: All quotations in `exact_quote` MUST be verbatim substrings from the source material above. Do not invent page numbers if not explicitly present."""


def build_task_classification_prompt(
    analysis: RequirementAnalysisResult,
    tasks_to_classify: list[dict[str, Any]],
    spec_text: str = "",
) -> str:
    """Build the user prompt for the Task Classification Engine."""
    formatted_tasks = []
    for t in tasks_to_classify:
        formatted_tasks.append(
            f"- [{t['task_id']}] {t['task_name']}: {t['description']}"
        )

    task_list_str = "\n".join(formatted_tasks)
    context_summary = f"Project: {analysis.project_name}\nSummary: {analysis.executive_summary}"

    return f"""Please classify the following software tasks into deterministic, ai_assisted, or agentic paradigms.

SYSTEM CONTEXT:
{context_summary}

CANDIDATE TASKS TO CLASSIFY:
{task_list_str}

ORIGINAL SOURCE TEXT (for evidence verification):
{spec_text[:4000] if spec_text else "Refer to extracted requirements and citations above."}

INSTRUCTIONS:
1. For every task in the list above, produce a `TaskClassification` item.
2. Select the paradigm (`deterministic`, `ai_assisted`, `agentic`) using rigorous, explainable criteria. Keep business rules and math in deterministic code!
3. Provide explicit `reasoning` explaining why this category was selected.
4. Attach `supporting_evidence` with verbatim citations from the source text where available.
5. Provide a realistic `confidence` score (0.0 to 1.0).
6. Detail realistic `risks` for each classification.
7. Determine `human_approval_required` based on whether the task triggers sensitive/irreversible actions.
8. Populate `summary_counts` with the total count for each category.
9. Return strictly valid JSON conforming to the schema."""


def build_architecture_search_prompt(
    analysis: RequirementAnalysisResult,
    classification: TaskClassificationResult | None = None,
    spec_text: str = "",
) -> str:
    """Build the prompt for generating the three distinct architecture candidates."""
    req_summary = []
    for req in analysis.functional_requirements:
        req_summary.append(f"- {req.req_id} ({req.priority}): {req.title} - {req.description}")

    rule_summary = []
    for rule in analysis.business_rules:
        rule_summary.append(f"- {rule.rule_id} [{rule.enforcement}]: {rule.description}")

    classification_context = ""
    if classification and classification.classifications:
        class_lines = []
        for c in classification.classifications:
            class_lines.append(f"- {c.task_name}: {c.category.value} (Approval required: {c.human_approval_required})")
        classification_context = f"\nTASK CLASSIFICATION BREAKDOWN:\n" + "\n".join(class_lines)

    return f"""Please generate exactly three distinct architecture candidates for the following software specification:

PROJECT: {analysis.project_name}
EXECUTIVE SUMMARY: {analysis.executive_summary}

KEY FUNCTIONAL REQUIREMENTS:
{chr(10).join(req_summary) if req_summary else "Refer to specification."}

CORE BUSINESS RULES:
{chr(10).join(rule_summary) if rule_summary else "Refer to specification."}
{classification_context}

ORIGINAL SPECIFICATION CONTEXT:
{spec_text[:3000] if spec_text else "Refer to requirements above."}

REQUIRED CANDIDATE STRUCTURE:
Generate exactly 3 candidates in `candidates`:
1. Candidate 1: `archetype` = 'conservative'
2. Candidate 2: `archetype` = 'hybrid_agentic'
3. Candidate 3: `archetype` = 'automation_heavy'

For each candidate, define:
- `candidate_id`: e.g. CAND-CONSERVATIVE, CAND-HYBRID, CAND-AUTOMATION
- `name`: Descriptive architecture title
- `summary`: Architectural thesis and philosophy
- `components`: Specific components with `component_id`, `name`, `type`, `responsibilities`, `technology_stack`
- `connections`: Component connections with `from_component_id`, `to_component_id`, `protocol`, `description`
- `data_flows`: End-to-end data flows with `flow_id`, `name`, and ordered `steps`
- `technology_assumptions`: Explicit tech stack assumptions
- `advantages`, `disadvantages`, `risks`: Realistic trade-offs
- `human_approval_points`: Explicit human oversight checkpoints
- `estimated_cost`: Monthly cost estimate with explicit usage assumptions
- `estimated_latency`: Expected p95 latency with network/model assumptions
- `complexity_score`: Number from 1.0 to 10.0
- `complexity_definition`: Clear definition of the complexity score basis

Return strictly valid JSON conforming to the `ArchitectureCandidatesResult` schema."""


def build_architecture_evaluation_prompt(
    candidates_result: ArchitectureCandidatesResult,
    analysis: RequirementAnalysisResult,
    weights_applied: dict[str, float],
) -> str:
    """Build the prompt for multi-criteria comparative evaluation."""
    candidate_summaries = []
    for cand in candidates_result.candidates:
        candidate_summaries.append(
            f"### [{cand.candidate_id}] {cand.name} (Archetype: {cand.archetype.value})\n"
            f"- Philosophy: {cand.summary}\n"
            f"- Components: {', '.join([c.name + ' (' + c.type + ')' for c in cand.components])}\n"
            f"- Estimated Cost: {cand.estimated_cost}\n"
            f"- Estimated Latency: {cand.estimated_latency}\n"
            f"- Complexity Score: {cand.complexity_score} ({cand.complexity_definition})\n"
            f"- Human Approval Points: {'; '.join(cand.human_approval_points)}\n"
            f"- Advantages: {'; '.join(cand.advantages)}\n"
            f"- Disadvantages: {'; '.join(cand.disadvantages)}\n"
            f"- Key Risks: {'; '.join(cand.risks)}"
        )

    weights_formatted = "\n".join([f"- {k}: {v:.2f}" for k, v in weights_applied.items()])

    return f"""Please evaluate and rank the following three architecture candidates across the agreed criteria:

PROJECT: {analysis.project_name}

CRITERIA WEIGHTS APPLIED:
{weights_formatted}

CANDIDATES TO EVALUATE:
{chr(10).join(candidate_summaries)}

INSTRUCTIONS:
1. Provide a `CandidateEvaluation` for each of the 3 candidates.
2. Evaluate each candidate on the 7 criteria:
   - `requirement_coverage`
   - `reliability`
   - `implementation_complexity`
   - `cost`
   - `latency`
   - `operational_risk`
   - `human_oversight`
3. Assign raw scores (0.0 to 10.0) where 10.0 is the best performing outcome.
4. Calculate `weighted_score = raw_score * weight`.
5. Sum weighted scores into `total_weighted_score`.
6. Select the candidate with the highest `total_weighted_score` as `selected_candidate_id`.
7. Detail `selection_rationale` explaining why this candidate scored highest under the selected criteria weights, explicitly noting that it is not claimed to be universally optimal.
8. Set `score_type` accurately ('heuristic', 'estimated', 'simulated', 'measured').

Return strictly valid JSON conforming to the `ArchitectureEvaluationResult` schema."""


SCENARIO_DESIGN_SYSTEM_PROMPT = """You are a Principal QA & Systems Resilience Architect for the Chrysalis AI platform.

Your task is to generate standardized, rigorous benchmark scenarios to evaluate and compare architecture candidates.

CRITICAL RULES:
1. CANONICAL CATEGORIES: You must produce scenarios covering all 6 canonical categories:
   - `normal_workflow`: Standard happy-path processing end-to-end under normal operating conditions.
   - `invalid_input`: Malformed documents, schema violations, invalid datatypes, or corrupted payloads.
   - `missing_information`: Incomplete forms, missing required fields, partial scans, or ambiguous data requiring extraction fallbacks.
   - `external_tool_failure`: Downstream network timeouts, third-party API 500 errors, rate-limiting, or database connection pool exhaustion.
   - `low_confidence_ai`: OCR ambiguities, conflicting multi-turn agent classifications, hallucination edge cases, or confidence scores below decision threshold.
   - `sensitive_human_approval`: High-value financial transactions, compliance risk events, data destruction, or actions mandating explicit human sign-off.

2. FAIR ARCHITECTURAL COMPARISON:
   - Scenarios must be defined objectively so that Conservative, Hybrid Agentic, and Automation-Heavy architectures can each be tested against the same scenario.
   - In each scenario's description and expected behavior, articulate how candidates with varying degrees of automation and determinism should respond.

3. EVIDENCE & REQUIREMENT GROUNDING:
   - Scenarios must be directly derived from the supplied project requirements, workflows, and business rules.
   - Never invent arbitrary requirements not implied or stated in the project context.
   - Do NOT simulate or claim measured execution outcomes; design the scenario test definition itself (inputs, expected behavior, evaluation criteria, failure conditions).

4. Return strictly valid JSON conforming to the `ScenarioDesignResult` schema without markdown wrappers."""


def build_scenario_design_prompt(
    analysis: RequirementAnalysisResult,
    candidates_result: ArchitectureCandidatesResult | None = None,
    classification: TaskClassificationResult | None = None,
    spec_text: str | None = None,
) -> str:
    """Build the prompt for designing standard evaluation scenarios."""
    req_summary = []
    for req in analysis.functional_requirements[:8]:
        req_summary.append(f"- [{req.req_id}] {req.title}: {req.description}")

    rule_summary = []
    for rule in analysis.business_rules[:6]:
        rule_summary.append(f"- [{rule.rule_id}] {rule.description} (Enforcement: {rule.enforcement})")

    candidate_context = ""
    if candidates_result and candidates_result.candidates:
        candidate_lines = []
        for cand in candidates_result.candidates:
            candidate_lines.append(
                f"- [{cand.candidate_id}] {cand.name} ({cand.archetype.value}): "
                f"Components: {', '.join([c.name for c in cand.components])}; "
                f"Human Approvals: {'; '.join(cand.human_approval_points) if cand.human_approval_points else 'None'}"
            )
        candidate_context = f"\n\nCANDIDATE ARCHITECTURES TO EVALUATE:\n" + "\n".join(candidate_lines)

    classification_context = ""
    if classification:
        human_approval_tasks = [
            t.task_name for t in classification.classifications if t.human_approval_required
        ]
        if human_approval_tasks:
            classification_context = f"\n\nTASKS REQUIRING HUMAN APPROVAL:\n- " + "\n- ".join(human_approval_tasks)

    return f"""Please design a comprehensive suite of benchmark scenarios for the following project:

PROJECT: {analysis.project_name}
EXECUTIVE SUMMARY: {analysis.executive_summary}

KEY FUNCTIONAL REQUIREMENTS:
{chr(10).join(req_summary) if req_summary else "Refer to specification."}

CORE BUSINESS RULES:
{chr(10).join(rule_summary) if rule_summary else "Refer to specification."}
{candidate_context}
{classification_context}

INSTRUCTIONS:
1. Generate at least 6 distinct benchmark scenarios covering ALL 6 canonical case types:
   - `normal_workflow`
   - `invalid_input`
   - `missing_information`
   - `external_tool_failure`
   - `low_confidence_ai`
   - `sensitive_human_approval`
2. For each scenario provide:
   - `scenario_id`: e.g. SCEN-01, SCEN-02, etc.
   - `case_type`: Exact canonical category name.
   - `title`: Short descriptive title of the test scenario.
   - `description`: Narrative of the scenario, initial conditions, and candidate architecture expectations.
   - `sample_input`: Realistic dictionary payload (e.g. headers, metadata, file attributes, invoice amount, etc.).
   - `expected_behavior`: Observable expected behavior of an acceptable architecture.
   - `evaluation_criteria`: List of explicit checkpoints determining pass/fail.
   - `failure_conditions`: List of explicit conditions that constitute a failure.
3. Provide a `benchmarking_guide` explaining how to execute and compare candidate architectures fairly against these scenarios.

Return strictly valid JSON conforming to the `ScenarioDesignResult` schema."""


CODE_GENERATION_SYSTEM_PROMPT = """You are a Principal Software Architect & Full-Stack Systems Engineer for the Chrysalis AI platform.

Your task is to generate complete, structured, compilable, and idiomatic project files conforming to the selected architecture candidate and project requirements.

CRITICAL RULES FOR CODE GENERATION:
1. REAL SOURCE FILES:
   - Output usable, real application source code, schemas, routers, service logic, configuration, and unit tests.
   - Do NOT emit placeholders, pseudo-code, ellipsis (...), or comments like '# todo: implement logic here'.
   - Implement real business logic and validation rules directly in the code.
2. ARCHITECTURAL FIDELITY:
   - Match the selected candidate archetype:
     * Conservative: 3-tier monolithic/modular structure with deterministic services, schemas, and relational database patterns.
     * Hybrid Agentic: Modular services with FastAPI gateway, asynchronous task workers, and targeted AI tool wrappers.
     * Automation-Heavy: Event-driven choreography, broker configuration, agent worker loops, and safety circuit breakers.
3. REQUIREMENT TRACEABILITY:
   - Explicitly implement the business rules and functional requirements from the specification.
   - For example, if a rule states invoices over $10,000 require manager approval, code that deterministic threshold check explicitly into the service logic and tests.
4. PATH SAFETY:
   - All `relative_path` entries must be safe relative paths (e.g. `app/main.py`, `app/schemas.py`, `app/services.py`, `tests/test_main.py`, `.env.example`, `requirements.txt`, `README.md`).
   - Never use absolute paths, Windows drive letters (C:), or directory traversal (`..`).
5. SECRETS HYGIENE:
   - NEVER embed live API keys, tokens, or credentials in any file.
   - Always read configuration from environment variables (e.g. `os.getenv` or Pydantic `BaseSettings`).
   - Provide an `.env.example` file with safe, descriptive placeholder values.
6. Return strictly valid JSON conforming to the `CodegenManifest` schema without markdown wrappers."""


def build_code_generation_prompt(
    selected_candidate: ArchitectureCandidate,
    analysis: RequirementAnalysisResult,
    classification: TaskClassificationResult | None = None,
    spec_text: str | None = None,
) -> str:
    """Build the prompt for generating actual project source files."""
    req_summary = []
    for req in analysis.functional_requirements[:8]:
        req_summary.append(f"- [{req.req_id}] {req.title}: {req.description}")

    rule_summary = []
    for rule in analysis.business_rules[:6]:
        rule_summary.append(f"- [{rule.rule_id}] {rule.description} (Enforcement: {rule.enforcement})")

    component_summary = []
    for comp in selected_candidate.components:
        component_summary.append(
            f"- [{comp.component_id}] {comp.name} ({comp.type}): "
            f"Stack: {comp.technology_stack}; Responsibilities: {', '.join(comp.responsibilities)}"
        )

    return f"""Please generate a complete, working project codebase for the selected architecture:

PROJECT: {analysis.project_name}
EXECUTIVE SUMMARY: {analysis.executive_summary}

SELECTED ARCHITECTURE CANDIDATE:
- Name: {selected_candidate.name}
- Archetype: {selected_candidate.archetype.value}
- Summary: {selected_candidate.summary}
- Target Stack: Python 3.12+ / FastAPI / Pydantic
- Components:
{chr(10).join(component_summary)}
- Human Approval Gates: {'; '.join(selected_candidate.human_approval_points) if selected_candidate.human_approval_points else 'None'}

FUNCTIONAL REQUIREMENTS TO IMPLEMENT:
{chr(10).join(req_summary) if req_summary else "Refer to specification."}

CORE BUSINESS RULES TO IMPLEMENT:
{chr(10).join(rule_summary) if rule_summary else "Refer to specification."}

REQUIRED PROJECT FILES:
Generate all required source files in `files`:
1. `requirements.txt`: Python package dependencies (fastapi, uvicorn, pydantic, pytest, etc.).
2. `.env.example`: Safe configuration template with placeholders.
3. Application package files (e.g. `app/__init__.py`, `app/main.py`, `app/schemas.py`, `app/services.py`).
4. Unit tests (e.g. `tests/__init__.py`, `tests/test_app.py`) verifying core requirements and business rules.
5. `README.md`: Documentation explaining architecture, components, and how to run tests.

Provide `setup_instructions` with step-by-step commands, and `completeness_notes` explaining the generated scope.

Return strictly valid JSON conforming to the `CodegenManifest` schema."""


# ==============================================================================
# Module W: Adaptive Requirement Wizard Prompts
# ==============================================================================

ADAPTIVE_WIZARD_SYSTEM_PROMPT = """You are Chrysalis AI's Adaptive Requirement Clarification Wizard (Module W).
Your objective is to inspect an extracted software specification and formulate between 3 and 5 context-aware multiple-choice questions.

Core principles:
1. Materiality: Ask ONLY questions that materially affect system architecture, autonomy boundaries, connector choices, and guardrails.
2. Core Categories to cover when relevant:
   - `goal`: What is the primary operational scope (e.g. informational query vs transaction orchestration)?
   - `autonomy`: How much autonomy is allowed (suggest only vs human-approved mutations vs low-risk autonomous execution)?
   - `connectors`: How will it interface with external systems (REST API, MCP server, database, or custom SDK)?
   - `data_mode`: What data environment will be used (synthetic test data, anonymized data, or approved live APIs)?
   - `constraints`: What hard operational constraints apply (latency budgets, write approval gates, audit requirements)?
3. Contextual Grounding: Reference actual modules, business rules, or risks identified in the specification.
4. Structured Options: Provide 2 to 4 clear options per question, each with an explicit `impact_summary`.
5. Return strictly valid JSON conforming to the `WizardQuestionnaire` schema."""


def build_adaptive_wizard_prompt(analysis: RequirementAnalysisResult) -> str:
    """Build user prompt for generating 3-5 context-aware adaptive wizard questions."""
    req_samples = [f"- {r.req_id}: {r.title}" for r in analysis.functional_requirements[:5]]
    rule_samples = [f"- {r.rule_id}: {r.description}" for r in analysis.business_rules[:4]]
    risk_samples = [f"- {r.item_id}: {r.description}" for r in analysis.risks_and_ambiguities[:3]]

    return f"""Please generate 3 to 5 high-impact adaptive clarification questions for this project:

PROJECT NAME: {analysis.project_name}
EXECUTIVE SUMMARY: {analysis.executive_summary}

KEY EXTRACTED REQUIREMENTS:
{chr(10).join(req_samples) if req_samples else "Standard software operational requirements."}

CORE BUSINESS RULES & CONSTRAINTS:
{chr(10).join(rule_samples) if rule_samples else "Standard compliance constraints."}

IDENTIFIED RISKS OR AMBIGUITIES:
{chr(10).join(risk_samples) if risk_samples else "Standard execution risks."}

INSTRUCTIONS:
Formulate between 3 and 5 questions covering goal, autonomy, connectors, data mode, and constraints.
Provide 2 to 4 options for each question with architectural impact summaries. Set `allow_custom: true`.
Return strictly valid JSON conforming to the `WizardQuestionnaire` schema."""


# ==============================================================================
# Module H: Explainable System Verdict Prompts
# ==============================================================================

SYSTEM_VERDICT_SYSTEM_PROMPT = """You are Chrysalis AI's Explainable System Verdict Engine (Module H).
Your objective is to evaluate a confirmed software specification and task classifications to determine the macro implementation verdict:
- `non-agentic`: The problem is predictable, rule-based, or deterministic. Solvable with conventional functions, rules engines, or APIs. An AI agent is unnecessary and introduces latency, cost, and reliability risks.
- `agentic`: The problem fundamentally requires open-ended reasoning, dynamic runtime planning, multi-step tool selection, or adapting to unpredictable inputs.
- `hybrid`: Some stages require flexible interpretation or AI assistance, while critical transactions, calculations, and mutations must remain deterministic and strictly gated.

Crucial rules:
1. Distinct Concept: This macro implementation verdict is NOT the same as the 3 architecture candidates (Conservative, Hybrid Agentic, Automation-Heavy). Do not confuse them.
2. Evidence-Based Reasoning: Ground your verdict in the task classification distribution and confirmed requirements. Never rely solely on a numerical score.
3. Human Oversight & Risk: If sensitive financial, account, or destructive actions exist, enforce human approval and prefer hybrid or non-agentic safeguards.
4. Return strictly valid JSON conforming to the `SystemVerdictResult` schema."""


def build_system_verdict_prompt(
    confirmed_spec: Any,
    classification: Any,
    analysis: Any = None,
) -> str:
    """Build user prompt for synthesizing an explainable system implementation verdict."""
    task_breakdown = []
    if hasattr(classification, "classifications"):
        for t in classification.classifications[:8]:
            task_breakdown.append(f"- [{t.category.value if hasattr(t.category, 'value') else t.category}] {t.task_name}: {t.reasoning}")

    summary_counts = getattr(classification, "summary_counts", {})
    constraints_summary = getattr(confirmed_spec, "constraints", {})

    return f"""Please evaluate the confirmed specification and task breakdown to produce an explainable system implementation verdict:

PROJECT: {confirmed_spec.project_name}
PRIMARY GOAL: {confirmed_spec.primary_goal}
AUTONOMY BOUNDARY: {confirmed_spec.autonomy_boundary}
DATA ENVIRONMENT: {confirmed_spec.data_mode}
CONNECTOR PREFERENCES: {', '.join(confirmed_spec.connector_preferences)}
CONSTRAINTS: {constraints_summary}

TASK BREAKDOWN:
{chr(10).join(task_breakdown) if task_breakdown else "Tasks classified according to requirements."}
SUMMARY COUNTS: {summary_counts}

INSTRUCTIONS:
1. Recommend an overall implementation verdict: 'non-agentic', 'agentic', or 'hybrid'.
2. Provide a compelling `headline` and comprehensive `reasoning` explaining the architectural decision.
3. Cite any relevant `supporting_evidence` references.
4. Explicitly list `assumptions`, `risks_and_limitations`, and state whether `human_approval_required` is true.
5. Provide a clear, actionable `recommended_next_step`.
6. Return strictly valid JSON conforming to the `SystemVerdictResult` schema."""


# ==============================================================================
# Phase 3: Test-Guided Code Repair Prompts
# ==============================================================================

CODE_REPAIR_SYSTEM_PROMPT = """You are Chrysalis AI's Test-Guided Code Repair Engine.
Your objective is to inspect failing source code, static validation errors, compiler/syntax tracebacks,
and test assertion failures, and propose targeted, safe, and minimal patches to fix the issues.

CRITICAL SAFETY & QUALITY CONSTRAINTS:
1. Strict Path Safety: You may only patch files within the provided project structure. Never introduce relative path escapes (..) or absolute paths.
2. Zero Secrets: Never insert API keys, passwords, secrets, or fake credentials. Use environment variable placeholders or standard mocking.
3. Clean Syntax: Any Python code must be syntactically valid and parse cleanly with `ast.parse`.
4. Minimal Changes: Propose only the minimal surgical fixes required to resolve the errors without rewriting unrelated business logic.
5. Return strictly valid JSON conforming to the requested schema containing the list of file patches."""


def build_code_repair_prompt(
    files: dict[str, str],
    diagnostics: list[str],
) -> str:
    """Build prompt for generating surgical repair patches for failing files."""
    file_snippets = []
    for path, content in list(files.items())[:5]:
        snippet = content[:1500] + ("\n...[truncated]" if len(content) > 1500 else "")
        file_snippets.append(f"--- FILE: {path} ---\n{snippet}\n")

    diag_summary = "\n".join(diagnostics[:10])

    return f"""Please analyze the following failure diagnostics and propose surgical patches to fix the errors:

DIAGNOSTICS & TEST FAILURES:
{diag_summary}

RELEVANT SOURCE FILES:
{''.join(file_snippets)}

INSTRUCTIONS:
1. Identify the root cause of the syntax, validation, or test assertion failures.
2. Propose patched content for each affected file.
3. Keep changes minimal and ensure Python syntax is 100% valid.
4. Do not insert any secrets or sensitive tokens.
5. Return JSON with key "patches": [ {{"file_path": "...", "content": "..."}} ]."""
