from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolCall(BaseModel):
    tool: str = Field(..., description="Name of tool called (e.g. get_weather)")
    arguments: Optional[Union[str, Dict[str, Any]]] = Field(
        "", description="Arguments passed to tool. Usually string."
    )
    result: Optional[Union[str, Dict[str, Any]]] = Field(
        None,
        description=(
            "Result returned by the tool. Can be null, a string, or dict"
        ),
    )
    timestamp: Optional[datetime] = Field(
        None, description="Optional ISO timestamp when the tool call completed"
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)


class AgentLog(BaseModel):
    instructions: Optional[str] = Field(
        None, description="The agents instructions / system prompt"
    )
    tools_available: List[str] = Field(
        default_factory=list, description="Tools that the agent could use"
    )
    tool_calls: List[ToolCall] = Field(
        default_factory=list, description="Chronological list of tool calls made by this agent"
    )
    output: Optional[str] = Field(None, description="Agent's textual output / response")
    duration_ms: Optional[int] = Field(
        None, description="Duration the agent ran for (milliseconds)"
    )


class Handoff(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_agent: Optional[str] = Field(None, alias="from", description="Agent handing off control")
    to_agent: Optional[str] = Field(None, alias="to", description="Agent receiving control")
    reason: Optional[str] = Field(None, description="Reason or short note about the handoff")
    timestamp: Optional[datetime] = Field(None, description="When the handoff occurred")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)


class TraceLog(BaseModel):
    """ Model for execution trace logs:

    - timestamp: when the trace started/was recorded
    - mode: execution mode (e.g., "concurrent" or "sequential") (will probably be handoff)
    - input: original user input
    - agents: mapping agent_name -> AgentLog
    - execution_order: ordered list of agent names that executed
    - handoffs: list of handoff events
    - final_output: full combined output after agent runs
    - duration_ms: total run duration (milliseconds)
    """

    timestamp: datetime = Field(..., description="ISO timestamp for the trace")
    mode: Optional[str] = Field(None, description="Execution mode (e.g. 'concurrent')")
    input: Optional[str] = Field(None, description="Original user input to the system")
    agents: Dict[str, AgentLog] = Field(
        default_factory=dict, description="Agent logs keyed by agent name"
    )
    execution_order: List[str] = Field(
        default_factory=list, description="Order in which agents ran"
    )
    handoffs: List[Handoff] = Field(
        default_factory=list, description="Recorded handoffs between agents"
    )
    final_output: Optional[str] = Field(None, description="Final combined output sent to user")
    duration_ms: Optional[int] = Field(None, description="Total execution duration in ms")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)
