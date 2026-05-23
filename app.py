from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from database import (save_medicines, load_medicines, reset_daily_status,
                      save_history, load_history, save_prescription,
                      load_prescription, delete_medicine)
from whatsapp import (send_medicine_taken, send_low_stock_alert,
                      send_missed_medicine, send_emergency,
                      send_daily_report, send_missed_daily_report)
from chatbot import get_medicine_response
import json, os, datetime, base64
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY", "medibridge_secret_2024")
CORS(app)

USERS_FILE = "users.json"

# ── User helpers ───────────────────────────────────────────────────────────────

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ── Auth API ───────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name     = data.get('name', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role     = data.get('role', 'senior')

    if not name or not username or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    users = load_users()
    if username in users:
        return jsonify({'success': False, 'error': 'Username already exists!'}), 400

    users[username] = {'password': password, 'role': role, 'name': name}
    save_users(users)
    return jsonify({'success': True, 'message': 'Registered successfully!'})

@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role     = data.get('role', 'senior')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Fill all fields!'}), 400

    users = load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'Username not found!'}), 401
    if users[username]['password'] != password:
        return jsonify({'success': False, 'error': 'Wrong password!'}), 401
    if users[username]['role'] != role:
        return jsonify({'success': False, 'error': f"This account is for {users[username]['role']}!"}), 403

    session['user'] = {'username': username, 'name': users[username]['name'], 'role': role}
    return jsonify({'success': True, 'user': session['user']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

# ── Medicines API ──────────────────────────────────────────────────────────────

@app.route('/api/medicines', methods=['GET'])
def get_medicines():
    medicines = reset_daily_status()
    return jsonify({'success': True, 'medicines': medicines})

@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    data = request.get_json()
    name          = data.get('name', '').strip()
    dosage        = data.get('dosage', '').strip()
    timing        = data.get('timing', 'Morning')
    total         = int(data.get('total', 30))
    notes         = data.get('notes', '')
    reminder_time = data.get('reminder_time', '')   # ← NEW: e.g. "08:00"

    if not name or not dosage:
        return jsonify({'success': False, 'error': 'Name and dosage required'}), 400

    medicines = load_medicines()
    medicines.append({
        'name': name, 'dosage': dosage, 'timing': timing,
        'total': total, 'remaining': total,
        'taken_today': False, 'notes': notes,
        'reminder_time': reminder_time              # ← NEW
    })
    save_medicines(medicines)
    save_history(name, 'Added')
    return jsonify({'success': True, 'medicines': medicines}), 201

@app.route('/api/medicines/<int:index>/take', methods=['POST'])
def take_medicine(index):
    medicines = load_medicines()
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404

    med = medicines[index]
    if med['taken_today']:
        return jsonify({'success': False, 'error': 'Already taken today'}), 400

    medicines[index]['taken_today'] = True
    medicines[index]['remaining'] = max(0, med['remaining'] - 1)
    save_medicines(medicines)
    save_history(med['name'], 'Taken')

    whatsapp_status = 'not_sent'
    low_stock = False
    try:
        send_medicine_taken(med['name'], med['dosage'], medicines[index]['remaining'])
        whatsapp_status = 'sent'
    except Exception as e:
        whatsapp_status = 'failed'

    if medicines[index]['remaining'] <= 5:
        low_stock = True
        try:
            send_low_stock_alert(med['name'], medicines[index]['remaining'])
        except:
            pass

    return jsonify({
        'success': True,
        'medicines': medicines,
        'whatsapp_status': whatsapp_status,
        'low_stock': low_stock
    })

@app.route('/api/medicines/<int:index>', methods=['DELETE'])
def remove_medicine(index):
    medicines = load_medicines()
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404
    name = medicines[index]['name']
    save_history(name, 'Deleted')
    updated = delete_medicine(index)
    return jsonify({'success': True, 'medicines': updated})

# ── History API ────────────────────────────────────────────────────────────────

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({'success': True, 'history': load_history()})

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    with open('history.json', 'w') as f:
        json.dump([], f)
    return jsonify({'success': True})

# ── Prescription API ───────────────────────────────────────────────────────────

@app.route('/api/prescription', methods=['GET'])
def get_prescription():
    return jsonify({'success': True, 'prescription': load_prescription()})

@app.route('/api/prescription', methods=['POST'])
def save_rx():
    data = request.get_json()
    if not data.get('patient_name') or not data.get('doctor_name'):
        return jsonify({'success': False, 'error': 'Patient and doctor name required'}), 400
    save_prescription(data)
    return jsonify({'success': True})

# ── Prescription Scanner API ───────────────────────────────────────────────────

@app.route('/api/scan-prescription', methods=['POST'])
def scan_prescription():
    data       = request.get_json()
    image_data = data.get('image_data', '')
    if not image_data:
        return jsonify({'success': False, 'error': 'No image provided'}), 400

    # Strip base64 header
    if ',' in image_data:
        img_b64 = image_data.split(',')[1]
        media_type = image_data.split(';')[0].split(':')[1]
    else:
        img_b64    = image_data
        media_type = 'image/jpeg'

    try:
        from groq import Groq

        # Use Groq vision to read prescription
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        message = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": """You are a medical prescription reader.
Carefully read this prescription image and extract all medicines.
Return ONLY a valid JSON array, nothing else. No explanation, no markdown.
Format exactly like this:
[
  {"name": "MedicineName", "dosage": "500mg", "timing": "Morning", "total": 30, "notes": "After food"},
  {"name": "AnotherMedicine", "dosage": "10mg", "timing": "Night", "total": 14, "notes": ""}
]
For timing use one of: Morning, Afternoon, Evening, Night, Morning & Night, Morning Afternoon & Night, After Food, Before Food.
If you cannot read the prescription clearly, return an empty array: []"""
                        }
                    ],
                }
            ],
        )

        raw = message.choices[0].message.content.strip()
        if '```' in raw:
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        
        medicines_found = json.loads(raw)
        
        if not isinstance(medicines_found, list):
            return jsonify({'success': False, 'error': 'Could not read prescription'}), 400

        # Auto-add all found medicines
        medicines = load_medicines()
        added = []
        for med in medicines_found:
            if med.get('name') and med.get('dosage'):
                new_med = {
                    'name':          med.get('name', ''),
                    'dosage':        med.get('dosage', ''),
                    'timing':        med.get('timing', 'Morning'),
                    'total':         int(med.get('total', 30)),
                    'remaining':     int(med.get('total', 30)),
                    'taken_today':   False,
                    'notes':         med.get('notes', ''),
                    'reminder_time': '',
                    'photo':         ''
                }
                medicines.append(new_med)
                save_history(new_med['name'], 'Added via Prescription Scan')
                added.append(new_med)

        if added:
            save_medicines(medicines)

        return jsonify({
            'success':  True,
            'found':    len(added),
            'medicines': added,
            'all_medicines': medicines
        })

    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Could not parse prescription. Please try a clearer image.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Drug Interaction Checker API ────────────────────────────────────────────────

@app.route('/api/check-interactions', methods=['POST'])
def check_interactions():
    medicines = load_medicines()
    if len(medicines) < 2:
        return jsonify({'success': True, 'interactions': [], 'message': 'Need at least 2 medicines to check interactions.'})

    med_names = [m['name'] + ' (' + m['dosage'] + ')' for m in medicines]
    med_list  = ', '.join(med_names)

    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """You are a pharmacist AI checking drug interactions.
Be concise, warm, and easy to understand for senior citizens.
Always end with: "Please consult your doctor before making any changes."
Return ONLY a JSON object, no markdown, no explanation:
{
  "has_interactions": true/false,
  "interactions": [
    {
      "medicines": ["Medicine A", "Medicine B"],
      "severity": "high/medium/low",
      "warning": "Short warning message",
      "advice": "What to do"
    }
  ],
  "safe_message": "Message if no interactions found"
}"""
                },
                {
                    "role": "user",
                    "content": f"Check drug interactions for these medicines: {med_list}"
                }
            ]
        )
        raw = response.choices[0].message.content.strip()
        if '```' in raw:
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        result = json.loads(raw)
        return jsonify({'success': True, **result})
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Could not parse response'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── Chatbot API ────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    data     = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'success': False, 'error': 'Empty question'}), 400
    medicines = load_medicines()
    try:
        response = get_medicine_response(question, medicines)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── WhatsApp API ───────────────────────────────────────────────────────────────

@app.route('/api/whatsapp/daily-report', methods=['POST'])
def daily_report():
    medicines = load_medicines()
    try:
        send_daily_report(medicines)
        return jsonify({'success': True, 'message': 'Daily report sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/whatsapp/emergency', methods=['POST'])
def emergency():
    try:
        send_emergency()
        return jsonify({'success': True, 'message': 'Emergency alert sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/whatsapp/check-missed', methods=['POST'])
def check_missed():
    medicines = load_medicines()
    current_hour = datetime.datetime.now().hour
    missed_meds = []
    for med in medicines:
        if not med['taken_today']:
            if med['timing'] == 'Morning' and current_hour >= 11:
                try:
                    send_missed_medicine(med['name'], med['timing'])
                    save_history(med['name'], 'Missed')
                    missed_meds.append(med['name'])
                except:
                    missed_meds.append(med['name'])
    return jsonify({'success': True, 'missed': missed_meds})

# ── Pill Photo API ─────────────────────────────────────────────────────────────

UPLOAD_FOLDER = os.path.join('static', 'pill_photos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/medicines/<int:index>/photo', methods=['POST'])
def upload_pill_photo(index):
    medicines = load_medicines()
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404
    data       = request.get_json()
    image_data = data.get('image_data', '')
    if not image_data:
        return jsonify({'success': False, 'error': 'No image data'}), 400
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    filename = f"pill_{index}_{medicines[index]['name'].replace(' ','_')}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(image_data))
    medicines[index]['photo'] = f'/static/pill_photos/{filename}'
    save_medicines(medicines)
    return jsonify({'success': True, 'photo': medicines[index]['photo'], 'medicines': medicines})

@app.route('/api/medicines/<int:index>/photo', methods=['DELETE'])
def delete_pill_photo(index):
    medicines = load_medicines()
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404
    photo_path = medicines[index].get('photo', '')
    if photo_path:
        full_path = photo_path.lstrip('/')
        if os.path.exists(full_path):
            os.remove(full_path)
        medicines[index]['photo'] = ''
        save_medicines(medicines)
    return jsonify({'success': True, 'medicines': medicines})

# ── Refill Request API ─────────────────────────────────────────────────────────

@app.route('/api/whatsapp/refill', methods=['POST'])
def refill_request():
    data = request.get_json()
    medicine_name = data.get('medicine_name', '')
    remaining     = data.get('remaining', 0)
    try:
        from twilio.rest import Client
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            from_="whatsapp:+14155238886",
            body=f"💊 *MediBridge — Refill Request*\n\n🛒 Please buy medicine:\n• Medicine: {medicine_name}\n• Only {remaining} tablets left!\n\nPlease refill as soon as possible! 🏥\n\n_Sent by MediBridge_",
            to=os.getenv("FAMILY_PHONE")
        )
        return jsonify({'success': True, 'message': 'Refill request sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── Rewards & Points API ───────────────────────────────────────────────────────

REWARDS_FILE = 'rewards.json'

def load_rewards():
    if os.path.exists(REWARDS_FILE):
        with open(REWARDS_FILE, 'r') as f:
            return json.load(f)
    return {'points': 0, 'streak': 0, 'last_date': '', 'badges': [], 'history': []}

def save_rewards(data):
    with open(REWARDS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

BADGES = [
    {'id': 'first_dose',  'name': 'First Dose!',      'emoji': '🌱', 'desc': 'Took your first medicine',     'points': 5},
    {'id': 'streak_3',    'name': '3-Day Streak!',     'emoji': '🔥', 'desc': '3 days all medicines taken',   'points': 10},
    {'id': 'streak_7',    'name': 'Week Warrior!',     'emoji': '⭐', 'desc': '7-day perfect streak',         'points': 20},
    {'id': 'streak_14',   'name': 'Fortnight Hero!',   'emoji': '🏅', 'desc': '14-day perfect streak',        'points': 35},
    {'id': 'streak_30',   'name': 'Monthly Champion!', 'emoji': '🏆', 'desc': '30-day perfect streak',        'points': 60},
    {'id': 'points_50',   'name': '50 Points Club!',   'emoji': '💎', 'desc': 'Earned 50 total points',       'points': 0},
    {'id': 'points_100',  'name': 'Century Club!',     'emoji': '👑', 'desc': 'Earned 100 total points',      'points': 0},
    {'id': 'all_taken',   'name': 'Perfect Day!',      'emoji': '✨', 'desc': 'All medicines taken in a day', 'points': 5},
]

@app.route('/api/rewards', methods=['GET'])
def get_rewards():
    return jsonify({'success': True, 'rewards': load_rewards(), 'badges': BADGES})

@app.route('/api/rewards/earn', methods=['POST'])
def earn_points():
    data    = request.get_json()
    reason  = data.get('reason', 'Medicine taken')
    pts     = int(data.get('points', 10))
    rewards = load_rewards()
    today   = str(datetime.date.today())
    rewards['points'] += pts
    rewards['history'].append({'reason': reason, 'points': pts, 'date': today})
    if rewards['last_date'] == str(datetime.date.today() - datetime.timedelta(days=1)):
        rewards['streak'] += 1
    elif rewards['last_date'] != today:
        rewards['streak'] = 1
    rewards['last_date'] = today
    newly_earned = []
    earned_ids   = [b['id'] for b in rewards['badges']]
    def award(badge_id):
        if badge_id not in earned_ids:
            badge = next((b for b in BADGES if b['id'] == badge_id), None)
            if badge:
                rewards['badges'].append({'id': badge['id'], 'name': badge['name'], 'emoji': badge['emoji'], 'date': today})
                rewards['points'] += badge['points']
                newly_earned.append(badge)
    if len(rewards['history']) == 1:   award('first_dose')
    if rewards['streak'] >= 3:         award('streak_3')
    if rewards['streak'] >= 7:         award('streak_7')
    if rewards['streak'] >= 14:        award('streak_14')
    if rewards['streak'] >= 30:        award('streak_30')
    if rewards['points'] >= 50:        award('points_50')
    if rewards['points'] >= 100:       award('points_100')
    medicines = load_medicines()
    if medicines and all(m['taken_today'] for m in medicines):
        award('all_taken')
    save_rewards(rewards)
    return jsonify({'success': True, 'rewards': rewards, 'newly_earned': newly_earned})

@app.route('/api/rewards/reset', methods=['POST'])
def reset_rewards():
    save_rewards({'points': 0, 'streak': 0, 'last_date': '', 'badges': [], 'history': []})
    return jsonify({'success': True})

# ── Appointments API ────────────────────────────────────────────────────────────

APPOINTMENTS_FILE = 'appointments.json'

def load_appointments():
    if os.path.exists(APPOINTMENTS_FILE):
        with open(APPOINTMENTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_appointments(data):
    with open(APPOINTMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    appts = load_appointments()
    today = datetime.date.today()
    for a in appts:
        try:
            appt_date = datetime.date.fromisoformat(a['date'])
            a['days_left'] = (appt_date - today).days
            a['status'] = 'today' if a['days_left'] == 0 else ('upcoming' if a['days_left'] > 0 else 'past')
        except:
            a['days_left'] = None
            a['status'] = 'unknown'
    return jsonify({'success': True, 'appointments': appts})

@app.route('/api/appointments', methods=['POST'])
def add_appointment():
    data     = request.get_json()
    doctor   = data.get('doctor', '').strip()
    hospital = data.get('hospital', '').strip()
    date     = data.get('date', '')
    time     = data.get('time', '')
    notes    = data.get('notes', '')
    if not doctor or not date:
        return jsonify({'success': False, 'error': 'Doctor name and date required'}), 400
    appts = load_appointments()
    appts.append({'id': str(len(appts)+1)+'_'+datetime.datetime.now().strftime('%H%M%S'),
                  'doctor': doctor, 'hospital': hospital, 'date': date,
                  'time': time, 'notes': notes, 'reminded': False})
    appts.sort(key=lambda x: x['date'])
    save_appointments(appts)
    return jsonify({'success': True, 'appointments': appts}), 201

@app.route('/api/appointments/<appt_id>', methods=['DELETE'])
def delete_appointment(appt_id):
    appts = [a for a in load_appointments() if a['id'] != appt_id]
    save_appointments(appts)
    return jsonify({'success': True, 'appointments': appts})

@app.route('/api/appointments/check-reminders', methods=['POST'])
def check_appointment_reminders():
    appts   = load_appointments()
    today   = datetime.date.today()
    sent    = []
    updated = False
    for i, a in enumerate(appts):
        try:
            days_left = (datetime.date.fromisoformat(a['date']) - today).days
            if days_left == 1 and not a.get('reminded', False):
                from twilio.rest import Client
                client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
                client.messages.create(
                    from_="whatsapp:+14155238886",
                    body=f"🏥 *MediBridge — Appointment Reminder*\n\n📅 Doctor appointment TOMORROW!\n\n👨‍⚕️ Doctor: {a['doctor']}\n🏥 Hospital: {a.get('hospital','N/A')}\n🕐 Time: {a.get('time','N/A')}\n📝 Notes: {a.get('notes','None')}\n\n_Please be prepared!_ 🌿\n_Sent by MediBridge_",
                    to=os.getenv("FAMILY_PHONE")
                )
                appts[i]['reminded'] = True
                updated = True
                sent.append(a['doctor'])
        except Exception as e:
            print(f"Appointment reminder error: {e}")
    if updated:
        save_appointments(appts)
    return jsonify({'success': True, 'sent': sent})

# ── Summary API ────────────────────────────────────────────────────────────────

@app.route('/api/summary', methods=['GET'])
def summary():
    medicines = load_medicines()
    total  = len(medicines)
    taken  = sum(1 for m in medicines if m['taken_today'])
    missed = total - taken
    low    = sum(1 for m in medicines if m['remaining'] <= 5)
    return jsonify({
        'success': True,
        'total': total, 'taken': taken,
        'missed': missed, 'low_stock': low,
        'last_updated': datetime.datetime.now().strftime('%I:%M %p')
    })

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')