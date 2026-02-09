"""
Multi-Agent API Integration Tests for CI/CD Pipeline
Tests individual agents and orchestrator workflows
"""

import os
import sys
import pytest
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.demos.code_assistant.orchestrator import orchestrator


@dataclass
class AgentTestResult: 
    """Test result container"""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    agent_used: Optional[str] = None

class AgentHealthChecker:
    """Health check utilities for individual agents"""
    
    @staticmethod
    def check_agent_response(response: str, expected_keywords: List[str]) -> bool:
        """
        Check if agent response contains expected keywords
        
        Args:
            response: Agent response text
            expected_keywords: List of keywords that should appear
            
        Returns:
            True if all keywords found, False otherwise
        """
        response_lower = response.lower()
        return all(keyword.lower() in response_lower for keyword in expected_keywords)
    
    @staticmethod
    def measure_response_time(func, *args, **kwargs) -> tuple:
        """
        Measure function execution time
        
        Returns:
            (result, duration_in_seconds)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration


class TestMultiAgentIntegration:
    """Integration tests for multi-agent system"""
    
    # Sample code for testing
    SAMPLE_CODE = """
def calculate(x, y):
    return x + y

def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
"""

    COMPLEX_CODE = """
class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    def filter_positive(self):
        return [x for x in self.data if x > 0]
    
    def transform(self, func):
        return [func(x) for x in self.data]
"""

    def setup_method(self):
        """Setup before each test"""
        self.health_checker = AgentHealthChecker()
        self.test_results: List[AgentTestResult] = []
    
    def teardown_method(self):
        """Cleanup after each test"""
        self._print_test_summary()
    
    def _capture_orchestrator_output(self, request: str, code: str) -> str:
        """
        Capture orchestrator output (non-streaming mode)
        """
        # TODO: Modify orchestrator to support non-streaming mode
        # For now, we'll need to capture stdout
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            orchestrator(request, code, stream=False)
        
        return captured_output.getvalue()
    
    def _record_result(self, test_name: str, passed: bool, duration: float, 
                      error: Optional[str] = None, agent: Optional[str] = None):
        """Record test result"""
        result = AgentTestResult(
            test_name=test_name,
            passed=passed,
            duration=duration,
            error_message=error,
            agent_used=agent
        )
        self.test_results.append(result)
    
    def _print_test_summary(self):
        """Print test execution summary"""
        print("\n" + "=" * 80)
        print("  TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        for result in self.test_results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            agent_info = f" [{result.agent_used}]" if result.agent_used else ""
            print(f"{status} {result.test_name}{agent_info} ({result.duration:.2f}s)")
            if result.error_message:
                print(f"      Error: {result.error_message}")
        
        print("-" * 80)
        print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
        print("=" * 80 + "\n")
    
    # ============================================================================
    # HEALTH CHECK TESTS
    # ============================================================================
    
    def test_orchestrator_basic_connectivity(self):
        """Test: Orchestrator basic connectivity"""
        test_name = "Orchestrator Basic Connectivity"
        
        try:
            start_time = time.time()
            # Simple request that should always work
            result = orchestrator("hello", "", stream=False)
            duration = time.time() - start_time
            
            # Should complete without exception
            self._record_result(test_name, True, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Orchestrator connectivity failed: {e}")
    
    def test_response_time_threshold(self):
        """Test: Response time within acceptable threshold"""
        test_name = "Response Time Threshold"
        threshold_seconds = 30.0  # Adjust based on your requirements
        
        try:
            start_time = time.time()
            orchestrator("Explain this code", self.SAMPLE_CODE, stream=False)
            duration = time.time() - start_time
            
            passed = duration < threshold_seconds
            error = None if passed else f"Response took {duration:.2f}s (threshold: {threshold_seconds}s)"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Response time test failed: {e}")
    
    # ============================================================================
    # INDIVIDUAL AGENT TESTS
    # ============================================================================
    
    def test_explainer_agent(self):
        """Test: Explainer agent functionality"""
        test_name = "Explainer Agent"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "What does this code do?",
                self.SAMPLE_CODE
            )
            duration = time.time() - start_time
            
            # Check for explanation-related keywords
            expected_keywords = ["function", "calculate", "process"]
            passed = self.health_checker.check_agent_response(output, expected_keywords)
            
            error = None if passed else "Expected keywords not found in explanation"
            self._record_result(test_name, passed, duration, error, "explainer")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "explainer")
            pytest.fail(f"Explainer agent test failed: {e}")
    
    def test_refactorer_agent(self):
        """Test: Refactorer agent functionality"""
        test_name = "Refactorer Agent"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "Refactor this code to improve readability",
                self.SAMPLE_CODE
            )
            duration = time.time() - start_time
            
            # Check for refactoring-related content
            expected_keywords = ["def", "return"]
            passed = self.health_checker.check_agent_response(output, expected_keywords)
            
            error = None if passed else "Refactored code not properly generated"
            self._record_result(test_name, passed, duration, error, "refactorer")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "refactorer")
            pytest.fail(f"Refactorer agent test failed: {e}")
    
    def test_documenter_agent(self):
        """Test: Documenter agent functionality"""
        test_name = "Documenter Agent"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "Add docstrings to this code",
                self.SAMPLE_CODE
            )
            duration = time.time() - start_time
            
            # Check for documentation-related content
            expected_keywords = ['"""', "Args:", "Returns:"]
            passed = self.health_checker.check_agent_response(output, expected_keywords)
            
            error = None if passed else "Docstrings not properly added"
            self._record_result(test_name, passed, duration, error, "documenter")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "documenter")
            pytest.fail(f"Documenter agent test failed: {e}")
    
    # ============================================================================
    # WORKFLOW INTEGRATION TESTS
    # ============================================================================
    
    def test_multi_step_workflow(self):
        """Test: Multi-agent workflow (refactor + document)"""
        test_name = "Multi-Step Workflow"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "Refactor this code and add documentation",
                self.SAMPLE_CODE
            )
            duration = time.time() - start_time
            
            # Should contain both refactoring and documentation
            refactor_keywords = ["def", "return"]
            doc_keywords = ['"""', "Args:"]
            
            passed = (
                self.health_checker.check_agent_response(output, refactor_keywords) and
                self.health_checker.check_agent_response(output, doc_keywords)
            )
            
            error = None if passed else "Multi-step workflow incomplete"
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Multi-step workflow test failed: {e}")
    
    def test_natural_language_understanding(self):
        """Test: Natural language query understanding"""
        test_name = "Natural Language Understanding"
        
        variations = [
            "Can you help me understand what's going on here?",
            "What's this code doing?",
            "Explain the logic"
        ]
        
        try:
            passed_count = 0
            total_duration = 0
            
            for query in variations:
                start_time = time.time()
                output = self._capture_orchestrator_output(query, self.SAMPLE_CODE)
                duration = time.time() - start_time
                total_duration += duration
                
                if "function" in output.lower() or "calculate" in output.lower():
                    passed_count += 1
            
            passed = passed_count == len(variations)
            error = None if passed else f"Only {passed_count}/{len(variations)} variations understood"
            
            self._record_result(test_name, passed, total_duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            self._record_result(test_name, False, 0, str(e), "orchestrator")
            pytest.fail(f"Natural language understanding test failed: {e}")
    
    def test_complex_code_handling(self):
        """Test: Complex code handling"""
        test_name = "Complex Code Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "Explain this code",
                self.COMPLEX_CODE
            )
            duration = time.time() - start_time
            
            # Should handle class-based code
            expected_keywords = ["class", "method", "DataProcessor"]
            passed = self.health_checker.check_agent_response(output, expected_keywords)
            
            error = None if passed else "Complex code not properly handled"
            self._record_result(test_name, passed, duration, error, "explainer")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "explainer")
            pytest.fail(f"Complex code handling test failed: {e}")
    
    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================
    
    def test_empty_code_handling(self):
        """Test: Empty code input handling"""
        test_name = "Empty Code Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "Explain this code",
                ""
            )
            duration = time.time() - start_time
            
            # Should handle gracefully without crashing
            passed = True  # If we got here, it didn't crash
            
            self._record_result(test_name, passed, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time
            # Empty code should be handled gracefully, not crash
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Empty code handling failed: {e}")
    
    def test_malformed_request_handling(self):
        """Test: Malformed request handling"""
        test_name = "Malformed Request Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "",  # Empty request
                self.SAMPLE_CODE
            )
            duration = time.time() - start_time
            
            # Should handle gracefully
            passed = True
            
            self._record_result(test_name, passed, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Malformed request handling failed: {e}")


# ============================================================================
# CI/CD INTEGRATION FUNCTIONS
# ============================================================================

def run_health_checks() -> Dict[str, bool]:
    """
    Run quick health checks for CI/CD pipeline
    
    Returns:
        Dictionary of agent names and their health status
    """
    health_status = {}
    
    # Basic connectivity check
    try:
        orchestrator("test", "def test(): pass", stream=False)
        health_status["orchestrator"] = True
    except Exception as e:
        print(f"❌ Orchestrator health check failed: {e}")
        health_status["orchestrator"] = False
    
    return health_status


def run_smoke_tests() -> bool:
    """
    Run minimal smoke tests for quick validation
    
    Returns:
        True if all smoke tests pass, False otherwise
    """
    print("\n🔥 Running Smoke Tests...")
    
    try:
        # Test 1: Basic explanation
        orchestrator("What does this do?", "def add(a, b): return a + b", stream=False)
        print("✓ Basic explanation test passed")
        
        # Test 2: Basic refactoring
        orchestrator("Refactor this", "def add(a, b): return a + b", stream=False)
        print("✓ Basic refactoring test passed")
        
        print("✅ All smoke tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Smoke tests failed: {e}\n")
        return False


if __name__ == "__main__":
    # Run smoke tests
    if not run_smoke_tests():
        sys.exit(1)
    
    # Run health checks
    health = run_health_checks()
    print("\n Health Check Results:")
    for agent, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {agent}: {'Healthy' if status else 'Unhealthy'}")
    
    # Run full test suite
    print("\n🧪 Running Full Test Suite...")
    pytest.main([__file__, "-v", "--tb=short"])
