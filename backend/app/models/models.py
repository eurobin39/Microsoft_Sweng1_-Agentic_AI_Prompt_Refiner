from __future__ import annotations
import json
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.trace_logs import TraceLog


class Provider(str, Enum):
    azure_openai = "azure_openai"
    openai = "openai"
    anthropic = "anthropic"
    mistral = "mistral"
    grok = "grok"

class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    markdown = "markdown"


class ModelParameters(BaseModel):
    """
    temperature, max_tokens, top_p are defined in schema.
    Schema allows additionalProperties: true so we allow extra keys here.
    """
    model_config = ConfigDict(extra="allow")

    temperature: float | None = Field(None, ge=0, le=2, description="0..2")
    max_tokens: int | None = Field(None, ge=1, description="min 1")
    top_p: float | None = Field(None, ge=0, le=1, description="0..1")


class Tool(BaseModel):
    """
    Tool items require 'name' and 'description'.
    Schema for each tool had additionalProperties: false -> forbid extras.
    parameters is arbitrary JSON (a JSON Schema object).
    """
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="What the tool does")
    parameters: Dict[str, Any] | None = Field(None, description="JSON Schema for tool input")

    @field_validator("parameters", mode="before")
    @classmethod
    def parse_parameters(cls, v):
        if isinstance(v, str) and v:
            return json.loads(v)
        return v


class AgentInfo(BaseModel):
    """
    'agent' object. system_prompt required by schema.
    additionalProperties: false -> forbid unknown fields.
    """
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, description="Human-readable name")
    description: str | None = Field(None, description="Short summary")
    system_prompt: str = Field(..., description="System prompt (required)")
    model: str | None = Field(None, description="Model identifier")
    provider: Provider | None = Field(None, description="LLM provider")
    model_parameters: ModelParameters | Dict[str, Any] | None = Field(
        None, description="Model-level config (may contain extra keys)"
    )
    tools: List[Tool] = Field(default_factory=list, description="List of tools")
    output_format: OutputFormat | None = Field(None, description="text/json/markdown")
    output_schema: Dict[str, Any] | None = Field(None, description="JSON Schema when output_format=json")

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, v):
        if isinstance(v, str):
            return v.replace("-", "_")
        return v

    @field_validator("model_parameters", "output_schema", mode="before")
    @classmethod
    def parse_json_objects(cls, v):
        if isinstance(v, str) and v:
            return json.loads(v)
        return v

    @model_validator(mode="after")
    def check_output_schema_if_json(self):
        if self.output_format == OutputFormat.json and not self.output_schema:
            raise ValueError("output_schema must be provided when output_format == 'json'")
        return self


class TestCase(BaseModel):
    """
     additionalProperties: false means forbid extras.
    'context' is arbitrary JSON goes to Dict[str, Any].
    """
    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(None, description="What this case checks")
    input: str = Field(..., description="User message sent to the agent (required)")
    expected_output: str | None = Field(None, description="Reference ideal output")
    expected_behavior: str | None = Field(None, description="Natural-language expected behavior")
    context: Dict[str, Any] | None = Field(None, description="Extra context (free-form)")

    @field_validator("context", mode="before")
    @classmethod
    def parse_context(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


class EvaluationCriteria(BaseModel):
    """
    goals and constraints are lists of strings. additionalProperties: false means forbid extras.
    """
    model_config = ConfigDict(extra="forbid")

    goals: List[str] = Field(default_factory=list, description="High-level qualities to optimize for")
    constraints: List[str] = Field(default_factory=list, description="Hard rules")
    priority_description: str | None = Field(None, description="What matters most / trade-offs")


class RefinementChange(BaseModel):
    """
    Represents a single modification applied to the blueprint.
    additionalProperties: false -> forbid extras.
    """
    model_config = ConfigDict(extra="forbid")

    issue_reference: str = Field(..., description="Reference to the issue identified by the judge")
    change_description: str = Field(..., description="Description of what was changed in the blueprint")
    reasoning: str = Field(..., description="Explanation of why this change was necessary")

class RefinementResult(BaseModel):
    """
    Structured output produced by the refiner.
    JSON-serialisable and enforces a strict schema.
    additionalProperties: false -> forbid extras.
    """
    model_config = ConfigDict(extra="forbid")

    refined_prompt: str = Field(..., description="Final improved version of the system prompt or blueprint")
    changes: List[RefinementChange] = Field(
        ..., description="List of modifications applied to the original blueprint"
    )
    expected_impact: str = Field(..., description="How the refinement improves performance")
    summary: str = Field(..., description="High-level summary of refinement rationale")


class AgentBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: AgentInfo = Field(..., description="Agent info (required)")
    test_cases: List[TestCase] = Field(..., description="List of test cases (required, min 1)")
    evaluation_criteria: EvaluationCriteria | None = Field(None, description="Optional evaluation guidance")

    @field_validator("evaluation_criteria", mode="before")
    @classmethod
    def parse_evaluation_criteria(cls, v):
        if isinstance(v, str) and v:
            return json.loads(v)
        return v

    @field_validator("test_cases")
    @classmethod
    def must_have_at_least_one_test_case(cls, v):
        if not v or len(v) < 1:
            raise ValueError("test_cases must contain at least one TestCase")
        return v

#wrapper for FastAPI router
class EvaluationRequest(BaseModel):
    blueprint: AgentBlueprint #agent info, test cases, etc.
    traces: list[TraceLog] #log model


class RefactorRequest(BaseModel):
    """
    Flexible ingestion contract for GenAI clients.
    Most fields are optional and extra keys are allowed.
    """
    model_config = ConfigDict(extra="allow")

    github_url: str | None = None
    repo_files: Dict[str, str] | List[Dict[str, Any]] | None = None
    raw_payload: Dict[str, Any] | str | None = None

    blueprint: Dict[str, Any] | str | None = None
    traces: List[Dict[str, Any]] | Dict[str, Any] | str | None = None

    # Minimal fallback fields when blueprint/traces are unavailable.
    agent_name: str | None = None
    system_prompt: str | None = None
    test_cases: List[Dict[str, Any]] | str | None = None
    test_inputs: List[str] | str | None = None
    observed_output: str | None = None

    include_normalized_payload: bool = Field(
        True,
        description="When true, returns normalized blueprint/traces preview in response."
    )


class TestCaseResult(BaseModel):
    """ Result for a single test case evaluation """
    test_case_description: str = Field(..., description="Description of the scenario being tested")
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0")
    passed: bool = Field(..., description="True if the agent passed the test criteria")
    reasoning: str = Field(..., description="Explanation of why this score was given")
    issues: List[str] = Field(default_factory=list, description="List of specific failures or bugs found")


class EvaluationResult(BaseModel):
    """ Overall evaluation result returned by the Judge """
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate score across all test cases")
    test_results: List[TestCaseResult] = Field(..., description="Detailed results for each test case")
    summary: str = Field(..., description="High-level diagnosis of the agent's performance")


class EvaluationResponse(BaseModel):
    """ Envelope returned by POST /evaluate — always contains the judge result,
        and optionally the refiner output when overall_score < 0.7. """
    evaluation: EvaluationResult = Field(..., description="Judge evaluation result")
    refinement: RefinementResult | None = Field(None, description="Refiner output (present when overall_score < 0.7)")


class RefactorResponse(BaseModel):
    evaluation: EvaluationResult = Field(..., description="Judge evaluation result")
    refinement: RefinementResult | None = Field(None, description="Refiner output if score is below threshold")
    normalized_blueprint: AgentBlueprint | None = Field(
        None,
        description="Server-normalized blueprint used for evaluation."
    )
    normalized_traces_count: int = Field(..., ge=0, description="Number of traces used after normalization")
    normalization_notes: List[str] = Field(default_factory=list, description="Normalization decisions for debugging")


class RefactorRunRequest(RefactorRequest):
    use_existing_traces: bool = Field(
        False,
        description="If true, append normalized incoming traces to generated runtime traces."
    )
    max_test_cases: int | None = Field(
        None,
        ge=1,
        description="Optional limit for number of blueprint test cases to execute at runtime."
    )
    include_generated_traces: bool = Field(
        True,
        description="When true, returns generated runtime traces in response."
    )


class RefactorRunResponse(BaseModel):
    evaluation: EvaluationResult = Field(..., description="Judge evaluation result")
    refinement: RefinementResult | None = Field(None, description="Refiner output if score is below threshold")
    normalized_blueprint: AgentBlueprint | None = Field(
        None,
        description="Normalized blueprint before runtime execution."
    )
    generated_traces: List[TraceLog] = Field(default_factory=list, description="Runtime-generated traces")
    traces_used_count: int = Field(..., ge=0, description="Number of traces used for judge/refiner")
    ground_truth_report: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-test precheck report built from runtime traces vs expected behavior/output."
    )
    normalization_notes: List[str] = Field(default_factory=list, description="Normalization and runtime notes")


class AgentRefinementResult(BaseModel):
    """Result for a single agent in a batch refinement run."""
    agent_name: str = Field(..., description="Name of the agent")
    evaluation: EvaluationResult = Field(..., description="Judge evaluation result")
    refinement: RefinementResult | None = Field(None, description="Refiner output if score < 0.7")


class AgentBlueprintWithTraces(BaseModel):
    blueprint: AgentBlueprint = Field(..., description="Extracted agent blueprint")
    traces: List[TraceLog] = Field(default_factory=list, description="Trace logs scraped from the repo for this agent")


class BatchRefineRequest(BaseModel):
    items: List[AgentBlueprintWithTraces] = Field(..., description="One blueprint+traces bundle per agent")
