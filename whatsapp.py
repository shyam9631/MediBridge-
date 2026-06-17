from twilio.rest import Client
from dotenv import load_dotenv
import os
import json

load_dotenv()

TWILIO_FROM = "whatsapp:+14155238886"


# ── Twilio client ─────────────────────────────────────────────────────────────

def _twilio():
    return Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))


# ── Get family phone numbers ──────────────────────────────────────────────────

def get_family_phones(username=None):
    """Get family WhatsApp numbers for a user from users.json, fallback to .env"""
    if username:
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
            phones = users.get(username, {}).get("family_phones", [])
            if phones:
                return [f"whatsapp:{p}" if not p.startswith("whatsapp:") else p for p in phones]
        except Exception:
            pass

    # Fallback to .env FAMILY_PHONE
    env_phone = os.getenv("FAMILY_PHONE", "")
    return [env_phone] if env_phone else []


# ── Send to all family members ────────────────────────────────────────────────

def send_to_all(body, username=None):
    phones  = get_family_phones(username)
    client  = _twilio()
    results = []

    if not phones:
        print(f"⚠️  No family phones found for user: {username}")
        return results

    for phone in phones:
        try:
            msg = client.messages.create(
                from_=TWILIO_FROM,
                body=body,
                to=phone
            )
            results.append({'phone': phone, 'sid': msg.sid, 'status': 'sent'})
        except Exception as e:
            results.append({'phone': phone, 'status': 'failed', 'error': str(e)})

    return results


# ── Notification functions ────────────────────────────────────────────────────

def send_medicine_taken(medicine_name, dosage, remaining, username=None):
    body = (
        f"💊 *MediBridge Alert*\n\n"
        f"✅ Medicine Taken!\n\n"
        f"👴 Your loved one just took:\n"
        f"• Medicine: {medicine_name}\n"
        f"• Dosage: {dosage}\n"
        f"• Remaining: {remaining} tablets\n\n"
        f"_Sent by MediBridge_ 🏥"
    )
    return send_to_all(body, username)


def send_low_stock_alert(medicine_name, remaining, username=None):
    body = (
        f"💊 *MediBridge Alert*\n\n"
        f"⚠️ Low Stock Warning!\n\n"
        f"• Medicine: {medicine_name}\n"
        f"• Only {remaining} tablets left!\n\n"
        f"Please refill soon! 🏥\n"
        f"_Sent by MediBridge_"
    )
    return send_to_all(body, username)


def send_missed_medicine(medicine_name, timing, username=None):
    body = (
        f"💊 *MediBridge Alert*\n\n"
        f"❌ Medicine Missed!\n\n"
        f"👴 Your loved one missed:\n"
        f"• Medicine: {medicine_name}\n"
        f"• Scheduled: {timing}\n\n"
        f"Please check on them! 🏥\n"
        f"_Sent by MediBridge_"
    )
    return send_to_all(body, username)


def send_emergency(username=None):
    body = (
        f"🚨 *EMERGENCY ALERT*\n\n"
        f"Your loved one needs immediate help!\n\n"
        f"Please call or visit them right away!\n\n"
        f"_Sent by MediBridge_ 🏥"
    )
    return send_to_all(body, username)


def send_daily_report(medicines, username=None):
    taken  = [m for m in medicines if m['taken_today']]
    missed = [m for m in medicines if not m['taken_today']]

    report  = "💊 *MediBridge Daily Report*\n\n"
    report += f"📊 *Today's Summary:*\n"
    report += f"✅ Taken: {len(taken)}/{len(medicines)} medicines\n"
    report += f"❌ Missed: {len(missed)} medicines\n\n"

    if taken:
        report += "*✅ Taken Today:*\n"
        for med in taken:
            report += f"  ✅ {med['name']} ({med['dosage']})\n"

    if missed:
        report += "\n*❌ Missed Today:*\n"
        for med in missed:
            report += f"  ❌ {med['name']} ({med['dosage']})\n"

    report += "\n_Sent by MediBridge_ 🏥"
    return send_to_all(report, username)


def send_missed_daily_report(medicines, username=None):
    taken  = [m for m in medicines if m['taken_today']]
    missed = [m for m in medicines if not m['taken_today']]

    body  = "💊 *MediBridge Daily Summary*\n\n"
    body += "⚠️ *Medicines Not Completed Today!*\n\n"
    body += f"📊 *Today's Report:*\n"
    body += f"✅ Taken: {len(taken)}/{len(medicines)} medicines\n"
    body += f"❌ Missed: {len(missed)} medicines\n\n"

    if taken:
        body += "*✅ Taken Today:*\n"
        for med in taken:
            body += f"  ✅ {med['name']} ({med['dosage']})\n"

    if missed:
        body += "\n*❌ Missed Today:*\n"
        for med in missed:
            body += f"  ❌ {med['name']} ({med['dosage']}) — {med['timing']}\n"

    body += "\n⚠️ *Please check on your loved one!*"
    body += "\n\n_Sent by MediBridge_ 🏥"
    return send_to_all(body, username)


def send_refill_request(medicine_name, remaining, username=None):
    body = (
        f"💊 *MediBridge — Refill Request*\n\n"
        f"🛒 Please buy medicine:\n"
        f"• Medicine: {medicine_name}\n"
        f"• Only {remaining} tablets left!\n\n"
        f"Please refill as soon as possible! 🏥\n\n"
        f"_Sent by MediBridge_"
    )
    return send_to_all(body, username)