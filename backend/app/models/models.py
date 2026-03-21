from __future__ import annotations
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
