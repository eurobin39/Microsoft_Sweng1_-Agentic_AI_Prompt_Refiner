# Resume Builder Multi-Agent Demo

This is a multi-agent system that generates tailored resumes by analyzing a user's background and a specific job description. It uses a workflow of three specialized agents (Profile Extractor, Job Analyst, and Resume Writer).

---

## ✅ Prerequisites (For Both Methods)

Before running the project, ensure you have the following:

1.  **Azure OpenAI Credentials**: 
    * Create a `.env` file in the `backend/` root directory.
    * Add your keys:
        ```env
        AZURE_OPENAI_API_KEY="your-key-here"
        AZURE_OPENAI_ENDPOINT="your-endpoint-here"
        AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
        ```

---

## 🚀 Option A: Run with Docker
*Use this method if you have Docker setup running.*

1.  **Navigate to the backend root:**
    ```bash
    cd backend
    ```

2.  **Build and Start the Container:**
    ```bash
    docker-compose up --build
    ```

3.  **Verify it is running:**
    The API will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💻 Option B: Run Locally (No Docker)
*Use this method if you're not using Docker.*

1.  **Prerequisites:**
    * Python 3.9 or higher installed.

2.  **Navigate to the backend root:**
    ```bash
    cd backend
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    # If on Mac/Linux and the above fails, try:
    # pip3 install -r requirements.txt
    ```

4.  **Start the Server:**
    Run the application using Uvicorn:
    ```bash
    python3 -m uvicorn app.main:app --reload
    ```

5.  **Verify it is running:**
    The API will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 How to Test (Swagger UI)

1.  Open your browser to the docs link (either `localhost:8000/docs` or `127.0.0.1:8000/docs`).
2.  Scroll down to the **Resume Demo** section.
3.  Click on the green bar: **POST /api/v1/resume-builder/generate**.
4.  Click **Try it out** (top right of the section).
5.  Paste the following JSON into the **Request body** box:

    ```json
    {
      "user_input": "I am a second/third-year student named XYZ. I know Python, FastAPI, and React. I built a travel agent AI last semester.",
      "job_description": "Junior Backend Developer needed. Must know Python and how to build APIs. Experience with AI agents is a plus."
    }
    ```

6.  Click the big blue **Execute** button.
7.  Scroll down to **Server response** to see your generated resume!

---

## 🛠 Troubleshooting

| Issue | Solution |
|-------|----------|
| **500 Internal Server Error** | Check your terminal logs. Usually means the `.env` file is missing or the Deployment Name is incorrect. |
| **404 Not Found** | Ensure you are sending the request to the correct URL (check the trailing slash). |
| **"Module not found"** | If running locally, ensure you installed `requirements.txt` in the correct virtual environment. |
| **Docker fails to start** | Make sure Docker Desktop is running and you are in the `backend/` folder before running `docker-compose`. |