import json
import os
import datetime

DATABASE_FILE = "medicines.json"
HISTORY_FILE = "history.json"

def save_medicines(medicines):
    with open(DATABASE_FILE, "w") as f:
        json.dump(medicines, f, indent=4)

def load_medicines():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            return json.load(f)
    return []

def reset_daily_status():
    medicines = load_medicines()
    today = str(datetime.date.today())
    last_reset_file = "last_reset.txt"

    if os.path.exists(last_reset_file):
        with open(last_reset_file, "r") as f:
            last_reset = f.read()
        if last_reset != today:
            for med in medicines:
                med["taken_today"] = False
            save_medicines(medicines)
            with open(last_reset_file, "w") as f:
                f.write(today)
    else:
        with open(last_reset_file, "w") as f:
            f.write(today)

    return medicines

def save_history(medicine_name, action):
    history = load_history()
    history.append({
        "medicine": medicine_name,
        "action": action,
        "time": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []