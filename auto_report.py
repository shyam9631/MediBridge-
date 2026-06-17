import schedule
import time
import json
import os
import datetime
from database import load_medicines
from whatsapp import send_daily_report, send_missed_daily_report

USERS_FILE = "users.json"


def load_all_seniors():
    """Read users.json and return list of all senior usernames."""
    if not os.path.exists(USERS_FILE):
        print("❌ users.json not found!")
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    seniors = [username for username, data in users.items() if data.get("role") == "senior"]
    return seniors


def send_nightly_report():
    now = datetime.datetime.now().strftime('%I:%M %p')
    print(f"\n{'='*45}")
    print(f"🕐 Running nightly report at {now}")
    print(f"{'='*45}\n")

    seniors = load_all_seniors()

    if not seniors:
        print("⚠️  No senior users found.")
        return

    print(f"👥 Found {len(seniors)} senior(s): {', '.join(seniors)}\n")

    for username in seniors:
        print(f"📋 Processing: {username}")
        try:
            medicines = load_medicines(username)

            if not medicines:
                print(f"   ⚠️  No medicines found for {username}\n")
                continue

            taken  = [m for m in medicines if m['taken_today']]
            missed = [m for m in medicines if not m['taken_today']]

            print(f"   Total: {len(medicines)} | ✅ Taken: {len(taken)} | ❌ Missed: {len(missed)}")

            if missed:
                send_missed_daily_report(medicines, username)
                print(f"   📲 Missed report sent to {username}'s family!\n")
            else:
                send_daily_report(medicines, username)
                print(f"   📲 All-clear report sent to {username}'s family!\n")

        except Exception as e:
            print(f"   ❌ Error for {username}: {e}\n")

    print("✅ Nightly report complete.\n")


# ── Schedule ──────────────────────────────────────────────────────────────────

# Runs every night at 10 PM
schedule.every().day.at("22:00").do(send_nightly_report)

# ── Uncomment the line below to test immediately when you run this file ───────
# send_nightly_report()

print("=" * 45)
print("   MediBridge Auto Reporter Running!")
print("   Nightly report sends at 10:00 PM")
print(f"   Started: {datetime.datetime.now().strftime('%d %b %Y, %I:%M %p')}")
print("=" * 45)

while True:
    schedule.run_pending()
    time.sleep(60)