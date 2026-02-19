from pathlib import Path
from datetime import datetime
import os
import json



def save_evaluation_result(agent_name: str, score: float, summary: str) -> bool:
    folder = "./evalutation.logs" #could be unsafe?
    file_name = agent_name + datetime.now().isoformat + ".json"
    file_path = os.path.join(folder, file_name) 
    data = {
        "agent" : agent_name,
        "agent score " : score,
        "retrieved at: " : datetime.now().isoformat,
        "Summary result" : summary
    }
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        return False





