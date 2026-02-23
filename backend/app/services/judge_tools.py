
from datetime import datetime
import os
import json


def save_evaluation_result(agent_name: str, score: float, summary: str) -> bool:
    folder = "./evaluation_logs" #could be unsafe?
    file_name = agent_name + datetime.now().isoformat() + ".json"
    file_path = os.path.join(folder, file_name) 
    data = {
        "agent" : agent_name,
        "agent_score " : score,
        "retrieved_at: " : datetime.now().isoformat(),
        "Summary_result" : summary
    }
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        return False





 