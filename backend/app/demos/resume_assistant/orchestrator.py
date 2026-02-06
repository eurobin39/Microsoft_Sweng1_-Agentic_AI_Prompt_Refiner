# Orchestrator - Runs all agents sequentially


import json
from app.services.llm.openai import OpenAIClient
from app.demos.resume_assistant.InfoCollector_agent import InfoCollectorAgent
from app.demos.resume_assistant.analysis_agent import JobAnalysisAgent
from app.demos.resume_assistant.resume_writing_agent import ResumeWriterAgent




class ResumeOrchestrator:


    def __init__(self):
        self.llm = OpenAIClient()
        self.collector = InfoCollectorAgent(self.llm)
        self.analyst = JobAnalysisAgent(self.llm)
        self.writer = ResumeWriterAgent(self.llm)


    async def run_pipeline(self, user_input: str, job_description: str):

        # Step 1: Collect User Info (should be json)
        print("--- Agent 1: Collecting Info (JSON) ---")
        user_profile_json = await self.collector.run(user_input)

        # Step 2: Analyze Job (should be json)
        print("--- Agent 2: Analyzing Job (JSON) ---")
        job_analysis_json = await self.analyst.run(job_description)

        # Step 3: Write Resume (Takes JSON strings, outputs Markdown)
        print("--- Agent 3: Writing Resume (Markdown) ---")

        # Passing the raw JSON strings directly to the writer, which is fine for the LLM to read
        final_resume = await self.writer.run(user_profile_json, job_analysis_json)

        # Return structured data as requested in screenshots
        return {
            "user_profile": json.loads(user_profile_json), # Parse to actual JSON object for API response
            "job_analysis": json.loads(job_analysis_json), # Parse to actual JSON object for API response
            "resume_markdown": final_resume
        }