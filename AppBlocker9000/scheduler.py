import json
import os
from datetime import datetime

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_rule(app_name, is_blocked):
    config = load_config()
    if app_name not in config:
        config[app_name] = {"start_hour": 0, "end_hour": 24}
    
    config[app_name]["is_blocked"] = is_blocked
    save_config(config)

def should_block(app_name):
    config = load_config()
    if app_name not in config:
        return False
    
    rules = config[app_name]
    if not rules.get("is_blocked", False):
        return False
    
    current_hour = datetime.now().hour
    if rules.get("start_hour", 0) <= current_hour < rules.get("end_hour", 24):
        return True
    return False