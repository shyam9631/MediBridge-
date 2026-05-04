import json
import os

# File where all medicines are saved
DATABASE_FILE = "medicines.json"

# Save medicines to file
def save_medicines(medicines):
    with open(DATABASE_FILE, "w") as f:
        json.dump(medicines, f, indent=4)

# Load medicines from file
def load_medicines():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            return json.load(f)
    return []