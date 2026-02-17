from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field, validator, root_validator


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
    temperature: float | None = Field(None, ge=0, le=2, description="0..2")
    max_tokens: int | None = Field(None, ge=1, description="min 1")
    top_p: float | None = Field(None, ge=0, le=1, description="0..1")

    class Config:
        extra = "allow"  # allow other keys not declared here


class Tool(BaseModel):
    """
    Tool items require 'name' and 'description'.
    Schema for each tool had additionalProperties: false -> forbid extras.
    parameters is arbitrary JSON (a JSON Schema object).
    """
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="What the tool does")
    parameters: Dict[str, Any] | None = Field(None, description="JSON Schema for tool input")

    class Config:
        extra = "forbid"


class AgentInfo(BaseModel):
    """
    'agent' object. system_prompt required by schema.
    additionalProperties: false -> forbid unknown fields.
    """
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

    class Config:
        extra = "forbid"

    @root_validator
    def check_output_schema_if_json(cls, values):
        fmt = values.get("output_format")
        schema = values.get("output_schema")
        if fmt == OutputFormat.json and not schema:
            raise ValueError("output_schema must be provided when output_format == 'json'")
        return values


class TestCase(BaseModel):
    """
     additionalProperties: false means forbid extras.
    'context' is arbitrary JSON goes to Dict[str, Any].
    """
    description: str | None = Field(None, description="What this case checks")
    input: str = Field(..., description="User message sent to the agent (required)")
    expected_output: str | None = Field(None, description="Reference ideal output")
    expected_behavior: str | None = Field(None, description="Natural-language expected behavior")
    context: Dict[str, Any] | None = Field(None, description="Extra context (free-form)")

    class Config:
        extra = "forbid"


class EvaluationCriteria(BaseModel):
    """
    goals and constraints are lists of strings. additionalProperties: false means forbid extras.
    """
    goals: List[str] = Field(default_factory=list, description="High-level qualities to optimize for")
    constraints: List[str] = Field(default_factory=list, description="Hard rules")
    priority_description: str | None = Field(None, description="What matters most / trade-offs")

    class Config:
        extra = "forbid"


class AgentBlueprint(BaseModel):
  
    agent: AgentInfo = Field(..., description="Agent info (required)")
    test_cases: List[TestCase] = Field(..., description="List of test cases (required, min 1)")
    evaluation_criteria: EvaluationCriteria | None = Field(None, description="Optional evaluation guidance")

    class Config:
        extra = "forbid"

    @validator("test_cases")
    def must_have_at_least_one_test_case(cls, v):
        if not v or len(v) < 1:
            raise ValueError("test_cases must contain at least one TestCase")
        return v
