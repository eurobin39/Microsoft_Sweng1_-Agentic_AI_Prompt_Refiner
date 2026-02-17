"""
Judge
TODO: Implement logic to aggregate feedback from multiple models
"""
import json
import asyncio
from typing import List, Dict, Any
from app.models import EvaluationResult
from app.services.llm.openai import OpenAIClient

class Judge:
    """Aggregates and judges feedback from multiple models
    Uses a mock structure for Blueprints until the real objects are ready..
    """

    def __init__(self):
        pass

    # TODO: Add judging and aggregation methods
    async def evaluate(self, blueprint: Dict[str, Any], traces: List[Dict[str, Any]]) -> EvaluationResult:
        """
        Scrutinizes agent execution traces against the Blueprint's test cases.
        """
        
        # 1. Extract Test Cases (Handling mock data structure)
        # assuming blueprint is a dictionary with a 'test_cases' key for now.
        test_cases = blueprint.get("test_cases", [])
        
        # 2. Constructing the Prompt
        prompt = self._construct_judge_prompt(test_cases, traces)
        
        # 3. Call the LLM
        # usinf 'json_object' mode instruction in the system prompt to ensure valid JSON.
        try:
            print("👨‍⚖️ Judge is evaluating...")
            response_text = await self.llm.generate(
                prompt=prompt,
                system_prompt=(
                    "You are an impartial AI QA Judge. "
                    "Your job is to validate if an AI Agent followed its instructions. "
                    "You must output ONLY valid JSON matching the requested format."
                )
            )
            
            # 4. Clean & Parse JSON
            # Remove potential markdown fences like ```json ... ```
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)
            
            # 5. Validate with the Pydantic Model from Part 1
            result = EvaluationResult(**data)
            return result

        except Exception as e:
            print(f"❌ Judge Evaluation Failed: {e}")
            # Return a generic failure object if LLM fails, so code doesn't crash
            return EvaluationResult(
                overall_score=0.0,
                test_results=[],
                summary=f"Internal Judge Error: {str(e)}"
            )

    def _construct_judge_prompt(self, test_cases: List[Dict], traces: List[Dict]) -> str:
        """Builds the context heavy prompt for the LLM."""
        return f"""
        ### TASK
        Review the "Conversation Traces" below and determine if the Agent satisfied the "Test Cases".
        
        ### 1. TEST CASES (The Rules)
        {json.dumps(test_cases, indent=2)}
        
        ### 2. CONVERSATION TRACES (The Reality)
        {json.dumps(traces, indent=2)}
        
        ### 3. OUTPUT FORMAT
        Respond with a JSON object strictly following this structure:
        {{
            "overall_score": <float 0.0-1.0>,
            "summary": "<string brief overview>",
            "test_results": [
                {{
                    "test_case_description": "<string from rules>",
                    "score": <float 0.0-1.0>,
                    "passed": <boolean>,
                    "reasoning": "<string explanation>",
                    "issues": ["<string issue 1>", "<string issue 2>"]
                }}
            ]
        }}
        """

# ==========================================
#  MOCK TEST RUNNER (Run this file directly)
# ==========================================
if __name__ == "__main__":
    # This allows you to test the Judge WITHOUT the real system....
    
    # 1. Mock Blueprint (What the agent WAS supposed to do)
    mock_blueprint = {
        "name": "TravelAssistant",
        "test_cases": [
            {
                "description": "Agent must ask for the user's budget.",
                "importance": "high"
            },
            {
                "description": "Agent must suggest at least 2 destinations.",
                "importance": "medium"
            }
        ]
    }

    # 2. Mock Traces (What the agent ACTUALLY did)
    # Scenario: Agent forgot to ask for budget.
    mock_traces = [
        {"role": "user", "content": "I want to go on a holiday."},
        {"role": "assistant", "content": "Great! Do you prefer beach or mountains?"},
        {"role": "user", "content": "Beach please."},
        {"role": "assistant", "content": "You should check out Bali or Maldives."}
    ]

    async def run_test():
        judge = Judge()
        result = await judge.evaluate(mock_blueprint, mock_traces)
        
        print("\n" + "="*30)
        print("🔎 JUDGE REPORT")
        print("="*30)
        print(f"Overall Score: {result.overall_score}")
        print(f"Summary: {result.summary}")
        print("-" * 20)
        for test in result.test_results:
            status = "✅ PASS" if test.passed else "❌ FAIL"
            print(f"{status}: {test.test_case_description}")
            print(f"   Reason: {test.reasoning}")

    # Run the async test
    asyncio.run(run_test())