"""
Resume Assistant Demo (MAF - Sequential)

Runs the MAF sequential workflow:
InfoCollector -> JobAnalyst -> ResumeWriter -> FeedbackAgent

How to run (from repo root):
    python -m backend.app.demos.resume_assistant.demo
"""

from __future__ import annotations

# IMPORTANT: when running with `python -m backend.app...`,
# imports must be absolute from `backend...`
from backend.app.demos.resume_assistant.runner import run_sync


def header(title: str) -> None:
    """Print a formatted header for the console output."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_demo() -> None:
    """Execute the full Resume Assistant sequential workflow demo."""
    # Sample user background info (unstructured)
    sample_user_background = """
My name is Sarah Johnson. I graduated from MIT with a B.S. in Computer Science in 2020.
I've been working as a backend developer at Stripe for 3 years, building payment
microservices in Python and Go. Before that I interned at Google on the Cloud team.
Skills: Python, Go, Java, PostgreSQL, Redis, Docker, Kubernetes, AWS.
I led a project migrating a monolith to microservices and reduced deploy times by 60%.
I have an AWS Solutions Architect certification.
I'm looking for a senior backend engineering role at a fast-growing startup.
""".strip()

    # Sample job description (unstructured)
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
""".strip()

    header("RESUME ASSISTANT — MAF SEQUENTIAL DEMO")

    print("🧑‍💼 Sample user background:")
    print("-" * 80)
    print(sample_user_background)
    print("-" * 80)

    print("\n📄 Sample job description:")
    print("-" * 80)
    print(sample_job_description)
    print("-" * 80)

    # Combine background and job posting into one prompt for the sequential pipeline.
    # The agents' instructions already dictate the 4 steps, but setting the goal helps the LLM.
    user_request = f"""
You are helping me with my resume.

[USER BACKGROUND]
{sample_user_background}

[JOB DESCRIPTION]
{sample_job_description}

Please write a tailored resume and review it.
""".strip()

    header("TEST 1: Full Sequential Pipeline (collect -> analyze -> write -> review)")
    
    # Run the workflow synchronously
    result = run_sync(user_request=user_request, stream=True)

    header("DEMO COMPLETE")
    
    # Display the participating agents from the trace
    print("🤖 Participating Agents:")
    participating_agents = result.get("agents", {}).keys()
    for agent in participating_agents:
        print(f" - {agent}")
        
    print("\nReturned keys:", list(result.keys()))
    print("\nFinal output preview:\n")
    
    final_text = result.get("final_output", "")
    print(final_text[:1200])
    
    if final_text and len(final_text) > 1200:
        print("\n... (truncated preview) ...\n")


if __name__ == "__main__":
    run_demo()