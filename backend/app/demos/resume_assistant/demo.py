import os
import sys

# Add the parent directory to Python path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from resume_assistant.orchestrator import orchestrator

def print_section_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def run_demo():
    # Sample user background info
    sample_user_input = """
    My name is Sarah Johnson. I graduated from MIT with a B.S. in Computer Science in 2020.
    I've been working as a backend developer at Stripe for 3 years, mostly building payment
    processing microservices in Python and Go. Before that I interned at Google on the Cloud
    team for a summer. I know Python, Go, Java, PostgreSQL, Redis, Docker, Kubernetes, and AWS.
    I led a project to migrate our monolith to microservices which reduced deploy times by 60%.
    I also have an AWS Solutions Architect certification. I'm looking for a senior backend
    engineering role at a fast-growing startup.
    """

    # Sample job description
    sample_job_description = """
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
    - Experience leading technical projects or mentoring junior engineers
    - Familiarity with event-driven architectures (Kafka, RabbitMQ)
    """

    print_section_header("RESUME BUILDER ORCHESTRATOR DEMO")
    print("Sample user input:")
    print("-" * 80)
    print(sample_user_input)
    print("-" * 80)
    print("\nSample job description:")
    print("-" * 80)
    print(sample_job_description)
    print("-" * 80)

    # Test 1: Full pipeline
    print_section_header("TEST 1: Full Pipeline - Build Resume From Scratch")
    print("User request: 'Build me a resume tailored to this job'\n")
    orchestrator("Build me a resume tailored to this job", sample_job_description, stream=True)

    # Test 2: Write only (user provides structured info directly)
    print_section_header("TEST 2: Write Only - Resume From Structured Data")
    print("User request: 'Just write me a resume with the info I gave you'\n")
    orchestrator("Just write me a resume with the info I gave you", sample_job_description, stream=True)

    # Test 3: Review only (user has an existing resume)
    sample_existing_resume = """
    # Sarah Johnson
    ## Backend Developer

    ### Experience
    - Backend Developer at Stripe (2021-Present)
      - Worked on payment services
      - Used Python and Go

    ### Education
    - B.S. Computer Science, MIT (2020)

    ### Skills
    Python, Go, AWS
    """
    print_section_header("TEST 3: Review Only - Feedback on Existing Resume")
    print("User request: 'Review my current resume against this job posting'\n")
    orchestrator(sample_existing_resume, sample_job_description, stream=True)

    # Test 4: Job analysis only
    print_section_header("TEST 4: Job Analysis Only")
    print("User request: 'Just analyze this job posting for me'\n")
    orchestrator("Just analyze this job posting for me", sample_job_description, stream=True)

    # Test 5: Natural language variation
    print_section_header("TEST 5: Natural Language Variation")
    print("User request: 'I need help making my resume stand out for this position'\n")
    orchestrator("I need help making my resume stand out for this position", sample_job_description, stream=True)

    print_section_header("DEMO COMPLETE")
    print("All test cases executed successfully! ✨\n")


if __name__ == "__main__":
    run_demo()