from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load credentials from .env file
load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
family_phone = os.getenv("FAMILY_PHONE")

client = Client(account_sid, auth_token)

def send_medicine_taken(medicine_name, dosage, remaining):
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        body=f"""
💊 *MediBridge Alert*

✅ Medicine Taken!

👴 Dad/Mom took their medicine:
- Medicine: {medicine_name}
- Dosage: {dosage}
- Remaining: {remaining} tablets

_Sent by MediBridge_ 🏥
        """,
        to=family_phone
    )
    return message.sid

def send_low_stock_alert(medicine_name, remaining):
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        body=f"""
💊 *MediBridge Alert*

⚠️ Low Stock Warning!

- Medicine: {medicine_name}
- Only {remaining} tablets left!

Please refill soon! 🏥

_Sent by MediBridge_
        """,
        to=family_phone
    )
    return message.sid

def send_missed_medicine(medicine_name, timing):
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        body=f"""
💊 *MediBridge Alert*

❌ Medicine Missed!

👴 Dad/Mom missed their medicine:
- Medicine: {medicine_name}
- Scheduled: {timing}

Please check on them! 🏥

_Sent by MediBridge_
        """,
        to=family_phone
    )
    return message.sid
def send_emergency():
    from twilio.rest import Client
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    client.messages.create(
        from_="whatsapp:+14155238886",
        body="🚨 *EMERGENCY ALERT*\n\nYour loved one needs immediate help!\n\nPlease call or visit them right away!\n\n_Sent by MediBridge_ 🏥",
        to=os.getenv("FAMILY_PHONE")
    )