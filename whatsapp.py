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
def send_daily_report(medicines):
    try:
        taken = [m for m in medicines if m['taken_today']]
        missed = [m for m in medicines if not m['taken_today']]

        report = "💊 *MediBridge Daily Report*\n\n"
        report += f"📊 *Today's Summary:*\n"
        report += f"✅ Taken: {len(taken)} medicines\n"
        report += f"❌ Missed: {len(missed)} medicines\n\n"

        if taken:
            report += "*Taken Today:*\n"
            for med in taken:
                report += f"✅ {med['name']} ({med['dosage']})\n"

        if missed:
            report += "\n*Missed Today:*\n"
            for med in missed:
                report += f"❌ {med['name']} ({med['dosage']})\n"

        report += "\n_Sent by MediBridge_ 🏥"

        message = client.messages.create(
            from_="whatsapp:+14155238886",
            body=report,
            to=family_phone
        )
        return message.sid
    except Exception as e:
        print(f"Error sending daily report: {e}")
        raise e
def send_missed_daily_report(all_medicines):
    try:
        taken = [m for m in all_medicines if m['taken_today']]
        missed = [m for m in all_medicines if not m['taken_today']]

        message_body = f"""💊 *MediBridge Daily Summary*

⚠️ *Medicines Not Completed Today!*

📊 *Today's Report:*
✅ Taken: {len(taken)}/{len(all_medicines)} medicines
❌ Missed: {len(missed)} medicines

"""
        if taken:
            message_body += "*✅ Taken Today:*\n"
            for med in taken:
                message_body += f"✅ {med['name']} ({med['dosage']})\n"

        if missed:
            message_body += "\n*❌ Missed Today:*\n"
            for med in missed:
                message_body += f"❌ {med['name']} ({med['dosage']}) - {med['timing']}\n"

        message_body += "\n⚠️ *Please check on your loved one!*"
        message_body += "\n\n_Sent by MediBridge_ 🏥"

        message = client.messages.create(
            from_="whatsapp:+14155238886",
            body=message_body,
            to=family_phone
        )
        return message.sid
    except Exception as e:
        print(f"Error: {e}")
        raise e