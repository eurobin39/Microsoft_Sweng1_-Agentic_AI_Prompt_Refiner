# 2nd Step.
# analysis Agent - Analyze job postings
# input - job posting text -> output - key requirements, skills, qualifications (structured data)

import json
from app.services.llm.openai import OpenAIClient


class JobAnalysisAgent:

    def __init__(self, llm: OpenAIClient):
        self.llm = llm

    async def run(self, job_description: str):
        system_prompt = """
        You are an expert Job Analyst.
        Analyze the JD and output a STRICT JSON summary.

        Output Format (JSON only):
        {
            "role": "Job Title",
            "required_skills": ["list of hard skills"],
            "preferred_skills": ["list of nice-to-have skills"],
            "keywords": ["ATS keywords"],
            "experience_level": "Junior/Mid/Senior",
            "domain": "Industry/Sector"
        }

        Do not include markdown formatting. Just return the raw JSON string.
        """

        response = await self.llm.generate(
            system_prompt=system_prompt,
            prompt=f"Job Description: {job_description}"
        )
        
        clean_response = response.replace("```json", "").replace("```", "").strip()
        return clean_response