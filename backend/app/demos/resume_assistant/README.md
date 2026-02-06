# Resume Builder Multi-Agent Demo

A multi-agent system that generates tailored resumes by analyzing user background and job descriptions.

## Environment Requirements
* **Python 3.9*** or **Docker**
* **Azure OpenAI Access**: Ensure your `.env` file in the root directory has valid `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` credentials.

## Setup Instructions
1.  Ensure the backend server is running:
    ```bash
    docker-compose up
    ```
2.  The endpoint will be available at: `http://localhost:8000/docs`

## Example Usage

**Request (POST):**
```json
{
  "user_input": "I am a backend engineer with 3 years of experience in Python and FastAPI. I built a travel agent AI last year.",
  "job_description": "We are looking for a Senior Python Developer to build AI agents using LangChain and Azure OpenAI."
}