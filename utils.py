import json
from datetime import datetime
from config import USERS_FILE, LOGS_FILE

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_user(name):
    data = load_users()
    data["last_id"] += 1
    user_id = f"user{data['last_id']}"

    data["users"][user_id] = {
        "name": name,
        "active": True,
        "banned": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    save_users(data)
    log_action(user_id, "create")
    return user_id

def log_action(user_id, action):
    try:
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append({
        "user": user_id,
        "action": action,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
