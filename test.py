from dotenv import load_dotenv
load_dotenv()
import os

print("SID:", os.getenv("TWILIO_ACCOUNT_SID"))
print("Token:", os.getenv("TWILIO_AUTH_TOKEN"))
print("Phone:", os.getenv("FAMILY_PHONE"))