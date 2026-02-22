from fastapi import APIRouter, HTTPException
import requests
import os
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()

EXTERNAL_SERVICES = [
    {
        "name": "Azure OpenAI Service",
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    }
    # More to be adedd
]

@router.get("/health")
def health_check():
    results = {"status": "ok", "external_services": []}

    for service in EXTERNAL_SERVICES:
        service_status = {
            "name": service["name"], 
            "status": "unreachable", 
            "error": None
        }

        try:
            headers = {"Authorization": f"Bearer {service['api_key']}"}
            response = requests.get(service["endpoint"], headers=headers)

            if response.status_code == 200:
                service_status["status"] = "reachable"
            else:
                service_status["status"] = "unreachable"
                service_status["error"] = f"Unexpected status code: {response.status_code}"

        except requests.exceptions.RequestException as e:
            service_status["status"] = "unreachable"
            service_status["error"] = f"Request failed: {str(e)}"

        results["external_services"].append(service_status)

    if any(service["status"] == "unreachable" for service in results["external_services"]):
        raise HTTPException(status_code=503, detail="One or more external services are unreachable")

    return results