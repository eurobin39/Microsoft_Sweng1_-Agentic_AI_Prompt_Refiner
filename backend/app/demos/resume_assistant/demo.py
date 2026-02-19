import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from resume_assistant.runner import run_workflow


SAMPLE_USER_INPUT = """
EURO BAE
Dublin, Ireland | +353 0834496428 | eurobin39@gmail.com

Education
Trinity College Dublin (September 2021 – May 2027)
- Honors bachelor's in integrated computer science
- Global Excellence Undergraduate Scholarship | Trinity International Foundation Scholarship
- Software Engineering Project Industry Award (Sustainability Award) | Huawei Tech Arena 2025 LLM Hackathon (3rd Prize)
- Relevant modules: Software Engineering Project, Computer Architecture and Information Management, Algorithms and Data Structures,
  Concurrent Systems, Statistical Analysis
- Joined DUCSS hackathons and coding competitions to strengthen collaborative problem-solving skills

Skills
- Languages & Programming: Java, Python, C, JavaScript, TypeScript, ARM, VHDL
- Web & Front-End Development: React, React Native, Tailwind, Next.js, HTML, CSS
- Back-End & DevOps: Node.js, Docker, Git, Linux, REST API
- Database & Cloud: PostgreSQL, MySQL, MongoDB, GraphQL, Oracle, AWS
- Tools & Monitoring: Grafana, Supabase, Cloudflare, OWASP ZAP, Zest, R, Expo Go
- Languages: Fluent in English and Korean

Employment
Undergraduate Demonstrator | Trinity College Dublin | Dublin (09/2025 – Present)
- Supported students in using Microsoft Expression Web 4, Python, and Excel for their coursework

Full Stack Engineer Intern (Industry-Academic Partnership) | Workday | Dublin (01/2025 – 04/2025)
- Developed and maintained both frontend (React) and backend (Node.js) components, contributing to over 80% of the codebase
- Established a CI/CD pipeline by configuring GitLab Runner on a Raspberry Pi, utilizing SSH tunneling for secure remote management
- Migrated database and server to Raspberry Pi, cutting energy use by ~93% and supporting green computing

Software Engineer Trainee | Samsung SDS | Suwon (02/2024 – 07/2024)
- Automated sample workflows using RPA tools during Samsung Bootcamp, improving task efficiency in demo environments
- Prototyped a smart factory system by combining RPA, ML, and IoT during Samsung RPA Bootcamp

Military Police Sergeant | Ministry of National Defense | Suwon (08/2022 – 02/2024)
- Conducted thorough investigations of potential breaches of military law and policy
- Utilized intelligence-gathering technology and implemented command structures to enhance operational efficiency

Data Analyst Intern | Media & Data Institute | Seoul (05/2021 – 09/2021)
- Refactored the data access layer by migrating from SQL to GraphQL, improving data flexibility and frontend integration
- Gained hands-on experience in data governance and privacy, collaborating on policies aligned with ethical data collection practices

Software Projects
A.T.M. (Automated Trading Manager)
- Built a Python-based trading bot integrating Binance API, executing automated trades based on technical signals and market conditions
- Implemented stop-loss and entry logic, improving simulated returns in test runs
- Analyzed transaction fees and macro indicators to optimize trade execution strategy

AURA (AI-based Work Efficiency Enhancer)
- Led a team of 5 to build an AI-powered productivity tracker platform combining webcam, mouse/keyboard data, and language models
- Integrated Azure Face API and OpenAI to assess concentration levels and generate productivity insights
- Conducted code reviews and finalized deployment, ensuring a cohesive UX across all integrated modules

OLY (Community-Driven Expat Platform)
- Led a 7-member development team, coordinating task allocation, version control, and technical decision-making, while deploying the app to
  TestFlight and Google Play internal testing
- Developed a full-stack community platform app using React Native, Expo, and Supabase, implementing marketplace, rental,
  currency exchange, chat, and authentication features
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
- Experience leading technical projects or mentoring junior engineers
- Familiarity with event-driven architectures (Kafka, RabbitMQ)
"""

LOG_FILE = "resume_assistant/log/resume_assistant.log"
TRACE_DIR = "resume_assistant/log/traces"


def header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_demo():
    header("RESUME ASSISTANT DEMO — GRAPH WORKFLOW")
    print(f"Traces will be saved to: {TRACE_DIR}/\n")

    run_workflow(
        user_input=SAMPLE_USER_INPUT,
        job_description=SAMPLE_JOB_DESCRIPTION,
        log_file=LOG_FILE,
        trace_dir=TRACE_DIR,
    )

    header("DEMO COMPLETE")
    print(f"Traces saved to: {TRACE_DIR}/\n")


if __name__ == "__main__":
    run_demo()
