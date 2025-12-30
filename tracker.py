import json
from datetime import datetime

LOG_FILE = "logs.json"

def log_event(user_id, action):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    logs.append({
        "user": user_id,
        "action": action,
        "time": datetime.now().isoformat()
    })

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
