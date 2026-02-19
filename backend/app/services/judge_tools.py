from pathlib import Path
from datetime import datetime
import json

def save_evaluation_result(agent_name: str, score: float, summary: str) -> str:
    """Write the evaluation result to a JSON log file."""



    
    # Name for each log you save might look like:
    # "{agent_name}_{timestamp_str}.json"
