"""
Resume Assistant API Integration Tests for CI/CD Pipeline
Tests 4-agent workflow: collect_info -> analyze_job -> write_resume -> review_resume
"""

import os
import sys
import pytest
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.demos.resume_assistant.orchestrator import orchestrator
from app.demos.resume_assistant.resume_info_collector_agent import collect_info
from app.demos.resume_assistant.resume_analysis_agent import analyze_job
from app.demos.resume_assistant.resume_writing_agent import write_resume
from app.demos.resume_assistant.resume_feedback_agent import review_resume


@dataclass
class ResumeTestResult:
    """Test result container for resume assistant"""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    agent_used: Optional[str] = None


class ResumeHealthChecker:
    """Health check utilities for resume assistant"""
    
    @staticmethod
    def check_response_quality(response: str, expected_keywords: List[str]) -> bool:
        """
        Check if resume response contains expected keywords
        
        Args:
            response: Agent response text
            expected_keywords: List of keywords that should appear
            
        Returns:
            True if all keywords found, False otherwise
        """
        response_lower = response.lower()
        return all(keyword.lower() in response_lower for keyword in expected_keywords)
    
    @staticmethod
    def check_resume_structure(response: str) -> bool:
        """
        Check if response contains basic resume structure elements
        
        Returns:
            True if structure is valid, False otherwise
        """
        required_sections = ["experience", "education", "skills"]
        response_lower = response.lower()
        return any(section in response_lower for section in required_sections)
    
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


class TestResumeAssistantIntegration:
    """Integration tests for resume assistant 4-agent system"""
    
    # Sample user background for testing
    SAMPLE_USER_INPUT = """
    My name is Sarah Johnson. I graduated from MIT with a B.S. in Computer Science in 2020.
    I've been working as a backend developer at Stripe for 3 years, mostly building payment
    processing microservices in Python and Go. Before that I interned at Google on the Cloud
    team for a summer. I know Python, Go, Java, PostgreSQL, Redis, Docker, Kubernetes, and AWS.
    I led a project to migrate our monolith to microservices which reduced deploy times by 60%.
    I also have an AWS Solutions Architect certification.
    """
    
    SAMPLE_JOB_DESCRIPTION = """
    Senior Backend Engineer - FinTech Startup

    We're looking for a Senior Backend Engineer to join our core platform team. You'll design
    and build scalable APIs and services that power our next-generation payments infrastructure.

    Requirements:
    - 3+ years of backend development experience
    - Strong proficiency in Python or Go
    - Experience with microservices architecture and distributed systems
    - Familiarity with cloud platforms (AWS preferred)
    - Experience with relational databases (PostgreSQL) and caching (Redis)
    - Understanding of CI/CD pipelines and containerization (Docker, Kubernetes)

    Nice to have:
    - Experience in fintech or payments
    - AWS certification
    - Experience leading technical projects
    """
    
    MINIMAL_USER_INPUT = """
    John Doe
    Software Engineer with 2 years experience
    Skills: Python, JavaScript
    """
    
    SIMPLE_JOB_DESCRIPTION = """
    Software Engineer
    Requirements: Python, JavaScript, 2+ years experience
    """

    def setup_method(self):
        """Setup before each test"""
        self.health_checker = ResumeHealthChecker()
        self.test_results: List[ResumeTestResult] = []
    
    def teardown_method(self):
        """Cleanup after each test"""
        self._print_test_summary()
    
    def _capture_orchestrator_output(self, user_input: str, job_description: str = "") -> str:
        """
        Capture orchestrator output (non-streaming mode)
        
        Args:
            user_input: User's background info or request
            job_description: Job posting text
        """
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            orchestrator(
                user_input=user_input,
                job_description=job_description,
                stream=False
            )
        
        return captured_output.getvalue()
    
    def _record_result(self, test_name: str, passed: bool, duration: float, 
                      error: Optional[str] = None, agent: Optional[str] = None):
        """Record test result"""
        result = ResumeTestResult(
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
        print("  RESUME ASSISTANT TEST SUMMARY")
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
                user_input="hello",
                job_description="test job",
                stream=False
            )
            duration = time.time() - start_time
            
            self._record_result(test_name, True, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Orchestrator connectivity failed: {e}")
    
    def test_response_time_threshold(self):
        """Test: Response time within acceptable threshold"""
        test_name = "Response Time Threshold"
        threshold_seconds = 60.0  # Resume full pipeline takes longer
        
        try:
            start_time = time.time()
            orchestrator(
                user_input=self.MINIMAL_USER_INPUT,
                job_description=self.SIMPLE_JOB_DESCRIPTION,
                stream=False
            )
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
    # INDIVIDUAL AGENT TESTS (4 agents)
    # ============================================================================
    
    def test_info_collector_agent(self):
        """Test: Info collector agent extracts structured data from user input"""
        test_name = "Info Collector Agent"
        
        try:
            start_time = time.time()
            output = collect_info(self.SAMPLE_USER_INPUT, stream=False)
            duration = time.time() - start_time
            
            # Check if output contains structured data (JSON-like)
            expected_keywords = ["education", "skills", "experience"]
            passed = self.health_checker.check_response_quality(output, expected_keywords)
            
            # Additional check: try to parse as JSON
            try:
                json.loads(output)
                passed = passed and True
            except:
                passed = False
            
            error = None if passed else "Failed to extract structured user info"
            self._record_result(test_name, passed, duration, error, "collector")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "collector")
            pytest.fail(f"Info collector test failed: {e}")
    
    def test_job_analysis_agent(self):
        """Test: Job analysis agent parses job requirements"""
        test_name = "Job Analysis Agent"
        
        try:
            start_time = time.time()
            output = analyze_job(self.SAMPLE_JOB_DESCRIPTION, stream=False)
            duration = time.time() - start_time
            
            # Check for job analysis structure
            expected_keywords = ["required_skills", "keywords", "experience_level"]
            passed = self.health_checker.check_response_quality(output, expected_keywords)
            
            # Try to parse as JSON
            try:
                parsed = json.loads(output)
                # Check if it has the expected structure
                passed = passed and ("required_skills" in parsed or "role" in parsed)
            except:
                passed = False
            
            error = None if passed else "Failed to analyze job description properly"
            self._record_result(test_name, passed, duration, error, "analyzer")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_result(test_name, False, duration, str(e), "analyzer")
            pytest.fail(f"Job analysis test failed: {e}")
    
    def test_resume_writer_agent(self):
        """Test: Resume writer generates resume from profile and job analysis"""
        test_name = "Resume Writer Agent"
        
        try:
            # First get the prerequisites
            user_profile = collect_info(self.SAMPLE_USER_INPUT, stream=False)
            job_analysis = analyze_job(self.SAMPLE_JOB_DESCRIPTION, stream=False)
            
            start_time = time.time()
            output = write_resume(user_profile, job_analysis, stream=False)
            duration = time.time() - start_time
            
            # Check for resume structure
            expected_keywords = ["experience", "education", "skills"]
            passed = self.health_checker.check_response_quality(output, expected_keywords)
            
            error = None if passed else "Generated resume missing essential sections"
            self._record_result(test_name, passed, duration, error, "writer")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "writer")
            pytest.fail(f"Resume writer test failed: {e}")
    
    def test_feedback_agent(self):
        """Test: Feedback agent reviews resume against job requirements"""
        test_name = "Feedback Agent"
        
        try:
            # Get prerequisites
            user_profile = collect_info(self.SAMPLE_USER_INPUT, stream=False)
            job_analysis = analyze_job(self.SAMPLE_JOB_DESCRIPTION, stream=False)
            resume = write_resume(user_profile, job_analysis, stream=False)
            
            start_time = time.time()
            output = review_resume(resume, job_analysis, stream=False)
            duration = time.time() - start_time
            
            # Check for feedback structure
            expected_keywords = ["strengths", "improvement", "score"]
            passed = self.health_checker.check_response_quality(output, expected_keywords)
            
            error = None if passed else "Feedback missing essential elements"
            self._record_result(test_name, passed, duration, error, "reviewer")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "reviewer")
            pytest.fail(f"Feedback agent test failed: {e}")
    
    # ============================================================================
    # WORKFLOW INTEGRATION TESTS
    # ============================================================================
    
    def test_full_pipeline_workflow(self):
        """Test: Full pipeline - collect -> analyze -> write -> review"""
        test_name = "Full Pipeline Workflow"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                user_input="Build me a resume tailored to this job",
                job_description=self.SAMPLE_JOB_DESCRIPTION
            )
            duration = time.time() - start_time
            
            # Should contain outputs from all 4 agents
            pipeline_check = all(keyword in output.lower() for keyword in 
                               ["profile", "analysis", "resume", "feedback"])
            
            passed = pipeline_check or self.health_checker.check_resume_structure(output)
            error = None if passed else "Full pipeline did not execute properly"
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Full pipeline test failed: {e}")
    
    def test_write_only_workflow(self):
        """Test: Write only workflow (skip info collection)"""
        test_name = "Write Only Workflow"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                user_input="Just write me a resume with the info I gave you",
                job_description=self.SAMPLE_JOB_DESCRIPTION
            )
            duration = time.time() - start_time
            
            passed = self.health_checker.check_resume_structure(output)
            error = None if passed else "Write-only workflow failed"
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Write-only workflow test failed: {e}")
    
    def test_natural_language_understanding(self):
        """Test: Natural language query understanding"""
        test_name = "Natural Language Understanding"
        
        variations = [
            "Help me create a resume",
            "I need to make a CV", 
            "Build me a professional resume",
        ]
        
        try:
            passed_count = 0
            total_duration = 0
            
            for query in variations:
                start_time = time.time()
                output = self._capture_orchestrator_output(
                    user_input=query,
                    job_description=self.SIMPLE_JOB_DESCRIPTION
                )
                duration = time.time() - start_time
                total_duration += duration
                
                if self.health_checker.check_resume_structure(output):
                    passed_count += 1
            
            passed = passed_count >= len(variations) - 1  # Allow 1 failure
            error = None if passed else f"Only {passed_count}/{len(variations)} variations understood"
            
            self._record_result(test_name, passed, total_duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            self._record_result(test_name, False, 0, str(e), "orchestrator")
            pytest.fail(f"Natural language understanding test failed: {e}")
    
    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================
    
    def test_empty_user_input_handling(self):
        """Test: Empty user input handling"""
        test_name = "Empty User Input Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                user_input="",
                job_description=self.SAMPLE_JOB_DESCRIPTION
            )
            duration = time.time() - start_time
            
            # Should handle gracefully without crashing
            passed = True  # If we got here, it didn't crash
            
            self._record_result(test_name, passed, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Empty user input handling failed: {e}")
    
    def test_empty_job_description_handling(self):
        """Test: Empty job description handling"""
        test_name = "Empty Job Description Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                user_input=self.MINIMAL_USER_INPUT,
                job_description=""  # Empty job description
            )
            duration = time.time() - start_time
            
            # Should still work or provide guidance
            passed = len(output) > 0
            error = None if passed else "No output for empty job description"
            
            self._record_result(test_name, passed, duration, error, "orchestrator")
            
            if not passed:
                pytest.fail(error)
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_result(test_name, False, duration, str(e), "orchestrator")
            pytest.fail(f"Empty job description handling failed: {e}")
    
    def test_malformed_request_handling(self):
        """Test: Malformed/unclear request handling"""
        test_name = "Malformed Request Handling"
        
        try:
            start_time = time.time()
            output = self._capture_orchestrator_output(
                user_input="asdfghjkl xyz 123",  # Garbage input
                job_description=self.SAMPLE_JOB_DESCRIPTION
            )
            duration = time.time() - start_time
            
            # Should handle gracefully (may classify as full_pipeline)
            passed = True
            
            self._record_result(test_name, passed, duration, agent="orchestrator")
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
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
        orchestrator(
            user_input="test",
            job_description="test job posting",
            stream=False
        )
        health_status["orchestrator"] = True
    except Exception as e:
        print(f" Resume orchestrator health check failed: {e}")
        health_status["orchestrator"] = False
    
    # Individual agent checks
    try:
        collect_info("Test user background", stream=False)
        health_status["collector"] = True
    except Exception as e:
        print(f" Info collector health check failed: {e}")
        health_status["collector"] = False
    
    try:
        analyze_job("Test job description", stream=False)
        health_status["analyzer"] = True
    except Exception as e:
        print(f" Job analyzer health check failed: {e}")
        health_status["analyzer"] = False
    
    return health_status


def run_smoke_tests() -> bool:
    """
    Run minimal smoke tests for quick validation
    
    Returns:
        True if all smoke tests pass, False otherwise
    """
    print("\n Running Resume Assistant Smoke Tests...")
    
    minimal_user = "John Doe, Software Engineer, Python"
    minimal_job = "Software Engineer position requiring Python"
    
    try:
        # Test 1: Info collection
        collect_info(minimal_user, stream=False)
        print("✓ Info collection test passed")
        
        # Test 2: Job analysis
        analyze_job(minimal_job, stream=False)
        print("✓ Job analysis test passed")
        
        # Test 3: Basic orchestrator
        orchestrator(
            user_input="Create a resume",
            job_description=minimal_job,
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
    print("\n📊 Health Check Results:")
    for agent, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {agent}: {'Healthy' if status else 'Unhealthy'}")
    
    # Run full test suite
    print("\n🧪 Running Full Test Suite...")
    pytest.main([__file__, "-v", "--tb=short"])
