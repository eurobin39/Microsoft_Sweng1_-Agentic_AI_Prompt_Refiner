# 3rd Step ( BUT VERY IMPORTANT ).
# Resume Writing Agent - Generate Resume Content
# input - structured user background info + key job requirements 
# -> output - Resume Text(Markdown or any structured format)


from app.services.llm.openai import OpenAIClient

class ResumeWriterAgent:
    
    def __init__(self, llm: OpenAIClient):
        self.llm = llm

    async def run(self, user_profile: str, job_analysis: str):
        system_prompt = """
        You are an expert Resume Writer.
        Write a professional resume in Markdown format.

        Instructions:
        - Use the 'User Profile' data provided.
        - Tailor the content to match the 'Job Analysis' keywords.
        - Use professional, action-oriented language.
        - Format neatly with Markdown headers (##).
        - Do NOT include placeholders like '[Your Name]' if the name is missing; just use generic headers.
        """

        return await self.llm.generate(
            system_prompt=system_prompt,
            prompt=f"User Profile: {user_profile}\n\nJob Analysis Requirements: {job_analysis}"
        )