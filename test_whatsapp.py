from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

sid   = os.getenv("TWILIO_ACCOUNT_SID")
token = os.getenv("TWILIO_AUTH_TOKEN")

print("SID:", sid)
print("Token:", token[:10]+"...")

client = Client(sid, token)

try:
    msg = client.messages.create(
        from_="whatsapp:+14155238886",
        body="🧪 Test from MediBridge!",
        to="whatsapp:+916366609752"
    )
    print("SUCCESS! Message SID:", msg.sid)
except Exception as e:
    print("ERROR:", str(e))