# 1st Step.
# analysis Agent - Gather user's background info
# input - User Conversation(natural language) -> output - structured data
# e.g., education, experience, skills, job preferences


import json
from app.services.llm.openai import OpenAIClient


class InfoCollectorAgent:

    def __init__(self, llm: OpenAIClient):
        self.llm = llm

    async def run(self, user_input: str):
        system_prompt = """
        You are an expert Resume Information Collector.
        Extract user details into a STRICT JSON format. 
        
        Output Format (JSON only):
            "name": "string or null",
            "education": ["list of strings"],
            "skills": ["list of strings"],
            "experience": ["list of strings"],
            "projects": ["list of strings"],
            "certifications": ["list of strings"],
            "summary": "brief professional summary string"

        Return ONLY the structured summary. Do not add conversational filler.
        """
        
        return await self.llm.generate(
            system_prompt=system_prompt,
            prompt=f"User Input: {user_input}"
        )
    
        # Clean up response to ensure valid JSON
        clean_response = response.replace("```json", "").replace("```", "").strip()
        return clean_response

