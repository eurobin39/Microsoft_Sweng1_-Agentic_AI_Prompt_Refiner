from typing import List, Optional
from pydantic import BaseModel, Field

class TestCaseResult(BaseModel):
    """Result for a single test case evaluation"""
    test_case_description: str = Field(..., description="Description of the scenario being tested")
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0")
    passed: bool = Field(..., description="True if the agent passed the test criteria")
    reasoning: str = Field(..., description="Explanation of why this score was given")
    issues: List[str] = Field(default_factory=list, description="List of specific failures or bugs found")

class EvaluationResult(BaseModel):
    """Overall evaluation result returned by the Judge"""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate score across all test cases")
    test_results: List[TestCaseResult] = Field(..., description="Detailed results for each test case")
    summary: str = Field(..., description="High-level diagnosis of the agent's performance")