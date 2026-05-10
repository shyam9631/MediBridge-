import schedule
import time
from database import load_medicines
from whatsapp import send_missed_daily_report
import datetime

def send_nightly_report():
    print(f"\n🕐 Running nightly report at {datetime.datetime.now().strftime('%I:%M %p')}")
    medicines = load_medicines()

    if not medicines:
        print("No medicines found!")
        return

    missed = [m for m in medicines if not m['taken_today']]
    taken = [m for m in medicines if m['taken_today']]

    print(f"Total: {len(medicines)} | Taken: {len(taken)} | Missed: {len(missed)}")

    if missed:
        try:
            send_missed_daily_report(medicines)
            print("✅ Missed medicine report sent to family!")
        except Exception as e:
            print(f"❌ Error sending report: {e}")
    else:
        print("✅ All medicines taken today! No alert needed!")

# Schedule report at 10 PM
schedule.every(2).minutes.do(send_nightly_report)

print("=" * 45)
print("   MediBridge Auto Reporter Running!")
print("   Daily report will send at 10:00 PM")
print("=" * 45)

while True:
    schedule.run_pending()
    time.sleep(60)