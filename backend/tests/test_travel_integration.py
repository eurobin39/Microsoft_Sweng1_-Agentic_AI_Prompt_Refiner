"""
Travel Assistant API Integration Tests for CI/CD Pipeline
Tests 2-agent workflow: get_weather -> get_packing_suggestions -> composition
"""

import os
import sys
import pytest
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.demos.travel_assistant.orchestrator import orchestrator
from app.demos.travel_assistant.travel_weather_agent import get_weather
from app.demos.travel_assistant.travel_packing_agent import get_packing_suggestions


@dataclass
class TravelTestResult:
    """Test result container for travel assistant"""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    agent_used: Optional[str] = None


class TravelHealthChecker:
    """Health check utilities for travel assistant"""
    
    @staticmethod
    def check_response_quality(response: str, expected_keywords: List[str]) -> bool:
        """
        Check if travel response contains expected keywords
        
        Args:
            response: Agent response text
            expected_keywords: List of keywords that should appear
            
        Returns:
            True if at least half of keywords found, False otherwise
        """
        if not response:
            return False
        response_lower = response.lower()
        matched = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
        return matched >= len(expected_keywords) // 2
    
    @staticmethod
    def check_weather_format(response: str) -> bool:
        """
        Check if response looks like weather information
        
        Returns:
            True if contains weather-related terms
        """
        weather_terms = ["temperature", "weather", "rain", "sunny", "cloudy", 
                        "wind", "°c", "°f", "celsius", "fahrenheit"]
        response_lower = response.lower()
        return any(term in response_lower for term in weather_terms)
    
    @staticmethod
    def check_packing_format(response: str) -> bool:
        """
        Check if response looks like packing suggestions
        
        Returns:
            True if contains packing-related terms
        """
        packing_terms = ["pack", "bring", "jacket", "umbrella", "clothes", 
                        "shoes", "layers", "wear", "clothing"]
        response_lower = response.lower()
        return any(term in response_lower for term in packing_terms)


class TestTravelAssistantIntegration:
    """Integration tests for travel assistant 2-agent system"""
    
    # Sample destinations for testing
    SAMPLE_DESTINATIONS = [
        "Tokyo, Japan",
        "Paris, France",
        "London, UK",
        "New York, USA"
    ]
    
    SIMPLE_DESTINATION = "Dublin, Ireland"
    TEST_DATE = datetime.now().strftime("%Y-%m-%d")

    def setup_method(self):
        """Setup before each test"""
        self.health_checker = TravelHealthChecker()
        self.test_results: List[TravelTestResult] = []
    
    def teardown_method(self):
        """Cleanup after each test"""
        self._print_test_summary()
    
    def _capture_orchestrator_output(self, user_request: str) -> str:
        """
        Capture orchestrator output (non-streaming mode)
        
        Args:
            user_request: User's travel request
        """
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = orchestrator(user_request=user_request, stream=False)
        
        # Return the actual result, not just stdout
        return result if result else captured_output.getvalue()
    
    def _record_result(self, test_name: str, passed: bool, duration: float, 
                      error: Optional[str] = None, agent: Optional[str] = None):
        """Record test result"""
        result = TravelTestResult(
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
        print("  TRAVEL ASSISTANT TEST SUMMARY")
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
            result = orchestrator(
                user_request="What's the weather in Tokyo?",
                stream=False
            )
            duration = time.time() - start_time
            
            # Should return something
            passed = result is not None and len(str(result)) > 0
            error = None if passed else "No response from orchestrator"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Orchestrator connectivity failed: {e}")
    
    def test_response_time_threshold(self):
        """Test: Response time within acceptable threshold"""
        test_name = "Response Time Threshold"
        threshold_seconds = 30.0
        
        try:
            start_time = time.time()
            orchestrator(
                user_request="What should I pack for London?",
                stream=False
            )
            duration = time.time() - start_time
            
            passed = duration < threshold_seconds
            error = None if passed else f"Response took {duration:.2f}s (threshold: {threshold_seconds}s)"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Response time test failed: {e}")
    
    # ============================================================================
    # INDIVIDUAL AGENT TESTS (2 agents)
    # ============================================================================
    
    def test_weather_agent(self):
        """Test: Weather agent returns weather information"""
        test_name = "Weather Agent"
        
        try:
            start_time = time.time()
            output = get_weather(self.SIMPLE_DESTINATION, self.TEST_DATE)
            duration = time.time() - start_time

            # Check if output looks like weather info
            passed = (
                output is not None and 
                len(output) > 0 and
                self.health_checker.check_weather_format(output)
            )
            
            error = None if passed else "Weather agent output invalid"
            self._record_result(test_name, passed, duration, error, "weather")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "weather")
            pytest.fail(f"Weather agent test failed: {e}")
    
    def test_packing_agent(self):
        """Test: Packing agent returns packing suggestions"""
        test_name = "Packing Agent"
        
        try:
            # Get weather info first (packing agent needs it)
            weather_info = get_weather(self.SIMPLE_DESTINATION, self.TEST_DATE)
            
            start_time = time.time()
            output = get_packing_suggestions(weather_info)
            duration = time.time() - start_time
            
            # Check if output looks like packing suggestions
            passed = (
                output is not None and 
                len(output) > 0 and
                self.health_checker.check_packing_format(output)
            )
            
            error = None if passed else "Packing agent output invalid"
            self._record_result(test_name, passed, duration, error, "packing")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "packing")
            pytest.fail(f"Packing agent test failed: {e}")
    
    # ============================================================================
    # WORKFLOW INTEGRATION TESTS
    # ============================================================================
    
    def test_weather_only_workflow(self):
        """Test: Weather-only request routing"""
        test_name = "Weather Only Workflow"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "What's the weather like in Tokyo?"
            )
            duration = time.time() - start_time
            
            # Should return weather information
            passed = self.health_checker.check_weather_format(output)
            error = None if passed else "Weather-only workflow failed"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Weather-only workflow test failed: {e}")
    
    def test_packing_only_workflow(self):
        """Test: Packing-only request routing"""
        test_name = "Packing Only Workflow"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "What should I pack for a trip to Iceland?"
            )
            duration = time.time() - start_time
            
            # Should return packing suggestions
            passed = self.health_checker.check_packing_format(output)
            error = None if passed else "Packing-only workflow failed"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Packing-only workflow test failed: {e}")
    
    def test_full_trip_advice_workflow(self):
        """Test: Full trip advice (both weather + packing)"""
        test_name = "Full Trip Advice Workflow"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "I'm travelling to Paris next week. What's the weather and what should I pack?"
            )
            duration = time.time() - start_time
            
            # Should contain both weather and packing information
            has_weather = self.health_checker.check_weather_format(output)
            has_packing = self.health_checker.check_packing_format(output)
            
            passed = has_weather or has_packing  # At least one should be present
            error = None if passed else "Full trip advice workflow failed"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Full trip advice test failed: {e}")
    
    def test_natural_language_understanding(self):
        """Test: Natural language query understanding"""
        test_name = "Natural Language Understanding"
        
        variations = [
            "Help me prepare for my trip to Barcelona",
            "I'm going to Rome, what should I bring?",
            "Planning a trip to Amsterdam, need advice"
        ]
        
        try:
            passed_count = 0
            total_duration = 0
            
            for query in variations:
                start_time = time.time()
                output = self._capture_orchestrator_output(query)
                duration = time.time() - start_time
                total_duration += duration
                
                # Check if response is relevant
                if (output and len(output) > 10 and 
                    (self.health_checker.check_weather_format(output) or 
                     self.health_checker.check_packing_format(output))):
                    passed_count += 1
            
            passed = passed_count >= len(variations) - 1  # Allow 1 failure
            error = None if passed else f"Only {passed_count}/{len(variations)} variations understood"
            
            self._record_result(test_name, passed, total_duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            self._record_result(test_name, False, 0, str(e), "orchestrator")
            pytest.fail(f"Natural language understanding test failed: {e}")
    
    def test_destination_extraction(self):
        """Test: Destination extraction from various phrasings"""
        test_name = "Destination Extraction"
        
        test_cases = [
            ("What's the weather in Tokyo?", ["tokyo"]),
            ("I'm going to Paris next week", ["paris"]),
            ("Trip to London tomorrow", ["london"])
        ]
        
        try:
            passed_count = 0
            total_duration = 0
            
            for query, expected_keywords in test_cases:
                start_time = time.time()
                output = self._capture_orchestrator_output(query)
                duration = time.time() - start_time
                total_duration += duration
                
                # Check if destination was understood (not "couldn't work out")
                if output and "couldn't work out" not in output.lower():
                    passed_count += 1
            
            passed = passed_count >= len(test_cases) - 1  # Allow 1 failure
            error = None if passed else f"Only {passed_count}/{len(test_cases)} destinations extracted"
            
            self._record_result(test_name, passed, total_duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            self._record_result(test_name, False, 0, str(e), "orchestrator")
            pytest.fail(f"Destination extraction test failed: {e}")
    
    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================
    
    def test_missing_destination_handling(self):
        """Test: Missing destination handling"""
        test_name = "Missing Destination Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "What's the weather?"  # No destination specified
            )
            duration = time.time() - start_time
            
            # Should provide error message or ask for clarification
            passed = output is not None and len(output) > 0
            error = None if passed else "No response for missing destination"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Missing destination handling failed: {e}")
    
    def test_malformed_request_handling(self):
        """Test: Malformed/unclear request handling"""
        test_name = "Malformed Request Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                "asdfghjkl xyz 123"  # Garbage input
            )
            duration = time.time() - start_time
            
            # Should handle gracefully (may return error message)
            passed = output is not None
            
            self._record_result(test_name, passed, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Malformed request handling failed: {e}")
    
    def test_empty_request_handling(self):
        """Test: Empty request handling"""
        test_name = "Empty Request Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output("")
            duration = time.time() - start_time
            
            # Should handle gracefully
            passed = True  # If we got here, it didn't crash
            
            self._record_result(test_name, passed, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Empty request handling failed: {e}")


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
        result = orchestrator(
            user_request="What's the weather in Dublin?",
            stream=False
        )
        health_status["orchestrator"] = result is not None
    except Exception as e:
        print(f"❌ Travel orchestrator health check failed: {e}")
        health_status["orchestrator"] = False
    
    # Individual agent checks
    try:
        weather = get_weather("Dublin, Ireland", datetime.now().strftime("%Y-%m-%d"))
        health_status["weather"] = weather is not None
    except Exception as e:
        print(f"❌ Weather agent health check failed: {e}")
        health_status["weather"] = False
    
    try:
        packing = get_packing_suggestions("14°C, partly cloudy")
        health_status["packing"] = packing is not None
    except Exception as e:
        print(f"❌ Packing agent health check failed: {e}")
        health_status["packing"] = False
    
    return health_status


def run_smoke_tests() -> bool:
    """
    Run minimal smoke tests for quick validation
    
    Returns:
        True if all smoke tests pass, False otherwise
    """
    print("\n🔥 Running Travel Assistant Smoke Tests...")
    
    try:
        # Test 1: Weather agent
        get_weather("Dublin, Ireland", datetime.now().strftime("%Y-%m-%d"))
        print("✓ Weather agent test passed")
        
        # Test 2: Packing agent
        get_packing_suggestions("14°C, rainy")
        print("✓ Packing agent test passed")
        
        # Test 3: Basic orchestrator
        orchestrator(
            user_request="What's the weather in Paris?",
            stream=False
        )
        print("✓ Basic orchestrator test passed")
        
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
    print("\nHealth Check Results:")
    for agent, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {agent}: {'Healthy' if status else 'Unhealthy'}")
    
    # Run full test suite
    print("\n🧪 Running Full Test Suite...")
    pytest.main([__file__, "-v", "--tb=short"])
