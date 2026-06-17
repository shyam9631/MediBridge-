import json
import os
import datetime

DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)


# ── Internal helper ───────────────────────────────────────────────────────────

def _path(username, filename):
    """Get the file path for a specific user's data file."""
    user_dir = os.path.join(DATA_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, filename)


# ── Medicines ─────────────────────────────────────────────────────────────────

def save_medicines(medicines, username):
    with open(_path(username, "medicines.json"), "w") as f:
        json.dump(medicines, f, indent=4)


def load_medicines(username):
    path = _path(username, "medicines.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def delete_medicine(index, username):
    medicines = load_medicines(username)
    if 0 <= index < len(medicines):
        medicines.pop(index)
        save_medicines(medicines, username)
    return medicines


def reset_daily_status(username):
    """Reset taken_today to False if it's a new day."""
    medicines  = load_medicines(username)
    today      = str(datetime.date.today())
    reset_path = _path(username, "last_reset.txt")

    if os.path.exists(reset_path):
        with open(reset_path, "r") as f:
            last_reset = f.read().strip()
        if last_reset != today:
            for med in medicines:
                med["taken_today"] = False
            save_medicines(medicines, username)
            with open(reset_path, "w") as f:
                f.write(today)
    else:
        with open(reset_path, "w") as f:
            f.write(today)

    return medicines


# ── History ───────────────────────────────────────────────────────────────────

def save_history(medicine_name, action, username):
    history = load_history(username)
    history.append({
        "medicine": medicine_name,
        "action":   action,
        "time":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    with open(_path(username, "history.json"), "w") as f:
        json.dump(history, f, indent=4)


def load_history(username):
    path = _path(username, "history.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def clear_history(username):
    with open(_path(username, "history.json"), "w") as f:
        json.dump([], f)


# ── Prescription ──────────────────────────────────────────────────────────────

def save_prescription(data, username):
    with open(_path(username, "prescription.json"), "w") as f:
        json.dump(data, f, indent=4)


def load_prescription(username):
    path = _path(username, "prescription.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


# ── Rewards ───────────────────────────────────────────────────────────────────

def load_rewards(username):
    path = _path(username, "rewards.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {'points': 0, 'streak': 0, 'last_date': '', 'badges': [], 'history': []}


def save_rewards(data, username):
    with open(_path(username, "rewards.json"), "w") as f:
        json.dump(data, f, indent=4)


# ── Appointments ──────────────────────────────────────────────────────────────

def load_appointments(username):
    path = _path(username, "appointments.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def save_appointments(data, username):
    with open(_path(username, "appointments.json"), "w") as f:
        json.dump(data, f, indent=4)