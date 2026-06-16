from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
from database import (save_medicines, load_medicines, reset_daily_status,
                      save_history, load_history, clear_history,
                      save_prescription, load_prescription, delete_medicine,
                      load_rewards, save_rewards, load_appointments, save_appointments)
from whatsapp import (send_medicine_taken, send_low_stock_alert,
                      send_missed_medicine, send_emergency,
                      send_daily_report, send_refill_request)
from chatbot import get_medicine_response
import json, os, datetime, base64
from dotenv import load_dotenv
import re as _re
import pytesseract
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH", "tesseract")
import random
import string

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY", "medibridge_secret_2024")
CORS(app)

USERS_FILE = "users.json"

def get_username():
    return session.get('user', {}).get('username', 'default')

def get_viewing_username():
    user = session.get('user', {})
    if user.get('role') == 'family':
        linked = user.get('linked_senior', '')
        return linked if linked else user.get('username', 'default')
    return user.get('username', 'default')

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')




# ── Auth ───────────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data          = request.get_json()
    name          = data.get('name', '').strip()
    username      = data.get('username', '').strip()
    password      = data.get('password', '').strip()
    role          = data.get('role', 'senior')
    family_phones = data.get('family_phones', [])
    link_code     = data.get('link_code', '').strip()

    if not name or not username or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    cleaned_phones = []
    for p in family_phones:
        p = p.strip().replace(' ', '').replace('-', '')
        if p and not p.startswith('+'):
            p = '+91' + p
        if p:
            cleaned_phones.append(p)

    users = load_users()
    if username in users:
        return jsonify({'success': False, 'error': 'Username already exists!'}), 400

    if role == 'senior':
        while True:
            code = 'MB-' + ''.join(random.choices(string.digits, k=6))
            code_exists = any(u.get('link_code') == code for u in users.values())
            if not code_exists:
                break

        users[username] = {
            'password':       password,
            'role':           role,
            'name':           name,
            'family_phones':  cleaned_phones,
            'link_code':      code,
            'linked_family':  []
        }

    elif role == 'family':
        if not link_code:
            return jsonify({'success': False, 'error': 'Please enter the senior\'s link code!'}), 400

        senior_username = None
        for uname, udata in users.items():
            if udata.get('link_code') == link_code and udata.get('role') == 'senior':
                senior_username = uname
                break

        if not senior_username:
            return jsonify({'success': False, 'error': 'Invalid link code! Ask your senior for their code.'}), 400

        users[username] = {
            'password':       password,
            'role':           role,
            'name':           name,
            'family_phones':  cleaned_phones,
            'linked_senior':  senior_username
        }

        if username not in users[senior_username]['linked_family']:
            users[senior_username]['linked_family'].append(username)

    save_users(users)
    return jsonify({
        'success':   True,
        'message':   'Registered successfully!',
        'link_code': users[username].get('link_code', '')
    })

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

    user_data = users[username]

    linked_senior_name     = ''
    linked_senior_username = ''
    if role == 'family':
        linked_senior_username = user_data.get('linked_senior', '')
        if linked_senior_username and linked_senior_username in users:
            linked_senior_name = users[linked_senior_username]['name']

    session['user'] = {
        'username':           username,
        'name':               user_data['name'],
        'role':               role,
        'family_phones':      user_data.get('family_phones', []),
        'link_code':          user_data.get('link_code', ''),
        'linked_senior':      linked_senior_username,
        'linked_senior_name': linked_senior_name,
        'linked_family':      user_data.get('linked_family', [])
    }
    return jsonify({'success': True, 'user': session['user']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/link-code', methods=['GET'])
def get_link_code():
    username = get_username()
    users    = load_users()
    code     = users.get(username, {}).get('link_code', '')
    linked   = users.get(username, {}).get('linked_family', [])

    family_members = []
    for fname in linked:
        if fname in users:
            family_members.append({
                'username': fname,
                'name':     users[fname]['name']
            })

    return jsonify({
        'success':        True,
        'link_code':      code,
        'family_members': family_members
    })

@app.route('/api/family-phones', methods=['GET'])
def get_family_phones_api():
    username = get_username()
    users    = load_users()
    phones   = users.get(username, {}).get('family_phones', [])
    return jsonify({'success': True, 'family_phones': phones})

@app.route('/api/family-phones', methods=['POST'])
def update_family_phones():
    username = get_username()
    data     = request.get_json()
    phones   = data.get('family_phones', [])
    cleaned  = []
    for p in phones:
        p = p.strip().replace(' ', '').replace('-', '')
        if p and not p.startswith('+'):
            p = '+91' + p
        if p:
            cleaned.append(p)
    users = load_users()
    users[username]['family_phones'] = cleaned
    save_users(users)
    return jsonify({'success': True, 'family_phones': cleaned})

# ── Medicines ──────────────────────────────────────────────────────────────────

@app.route('/api/medicines', methods=['GET'])
def get_medicines():
    u = get_viewing_username()
    medicines = reset_daily_status(u)
    return jsonify({'success': True, 'medicines': medicines})

@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    data          = request.get_json()
    name          = data.get('name', '').strip()
    dosage        = data.get('dosage', '').strip()
    timing        = data.get('timing', 'Morning')
    total         = int(data.get('total', 30))
    notes         = data.get('notes', '')
    reminder_time = data.get('reminder_time', '')

    if not name or not dosage:
        return jsonify({'success': False, 'error': 'Name and dosage required'}), 400

    u = get_username()
    medicines = load_medicines(u)
    medicines.append({
        'name': name, 'dosage': dosage, 'timing': timing,
        'total': total, 'remaining': total,
        'taken_today': False, 'notes': notes,
        'reminder_time': reminder_time, 'photo': ''
    })
    save_medicines(medicines, u)
    save_history(name, 'Added', u)
    return jsonify({'success': True, 'medicines': medicines}), 201

@app.route('/api/medicines/<int:index>/take', methods=['POST'])
def take_medicine(index):
    u = get_username()
    medicines = load_medicines(u)
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404

    med = medicines[index]
    if med['taken_today']:
        return jsonify({'success': False, 'error': 'Already taken today'}), 400

    medicines[index]['taken_today'] = True
    medicines[index]['remaining']   = max(0, med['remaining'] - 1)
    save_medicines(medicines, u)
    save_history(med['name'], 'Taken', u)

    whatsapp_status = 'not_sent'
    low_stock       = False
    try:
        send_medicine_taken(med['name'], med['dosage'], medicines[index]['remaining'], u)
        whatsapp_status = 'sent'
    except Exception:
        whatsapp_status = 'failed'

    if medicines[index]['remaining'] <= 5:
        low_stock = True
        try:
            send_low_stock_alert(med['name'], medicines[index]['remaining'], u)
        except Exception:
            pass

    return jsonify({
        'success': True, 'medicines': medicines,
        'whatsapp_status': whatsapp_status, 'low_stock': low_stock
    })

@app.route('/api/medicines/<int:index>', methods=['DELETE'])
def remove_medicine(index):
    u = get_username()
    medicines = load_medicines(u)
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404
    name = medicines[index]['name']
    save_history(name, 'Deleted', u)
    updated = delete_medicine(index, u)
    return jsonify({'success': True, 'medicines': updated})

# ── Pill Photo ─────────────────────────────────────────────────────────────────

UPLOAD_FOLDER = os.path.join('static', 'pill_photos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/medicines/<int:index>/photo', methods=['POST'])
def upload_pill_photo(index):
    u = get_username()
    medicines = load_medicines(u)
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404
    data       = request.get_json()
    image_data = data.get('image_data', '')
    if not image_data:
        return jsonify({'success': False, 'error': 'No image data'}), 400
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    filename = f"pill_{u}_{index}_{medicines[index]['name'].replace(' ','_')}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(image_data))
    medicines[index]['photo'] = f'/static/pill_photos/{filename}'
    save_medicines(medicines, u)
    return jsonify({'success': True, 'photo': medicines[index]['photo'], 'medicines': medicines})

@app.route('/api/medicines/<int:index>/photo', methods=['DELETE'])
def delete_pill_photo(index):
    u = get_username()
    medicines = load_medicines(u)
    if index < 0 or index >= len(medicines):
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404
    photo_path = medicines[index].get('photo', '')
    if photo_path:
        full_path = photo_path.lstrip('/')
        if os.path.exists(full_path):
            os.remove(full_path)
        medicines[index]['photo'] = ''
        save_medicines(medicines, u)
    return jsonify({'success': True, 'medicines': medicines})

# ── History ────────────────────────────────────────────────────────────────────

@app.route('/api/history', methods=['GET'])
def get_history():
    u = get_viewing_username()
    return jsonify({'success': True, 'history': load_history(u)})

@app.route('/api/history', methods=['DELETE'])
def clear_history_api():
    clear_history(get_username())
    return jsonify({'success': True})

# ── Prescription ───────────────────────────────────────────────────────────────

@app.route('/api/prescription', methods=['GET'])
def get_prescription():
    u = get_viewing_username()
    return jsonify({'success': True, 'prescription': load_prescription(u)})

@app.route('/api/prescription', methods=['POST'])
def save_rx():
    data = request.get_json()
    if not data.get('patient_name') or not data.get('doctor_name'):
        return jsonify({'success': False, 'error': 'Patient and doctor name required'}), 400
    save_prescription(data, get_username())
    return jsonify({'success': True})

# ── Chatbot ────────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    data     = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'success': False, 'error': 'Empty question'}), 400
    medicines = load_medicines(get_viewing_username())
    try:
        response = get_medicine_response(question, medicines)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── Prescription Scanner ───────────────────────────────────────────────────────

@app.route('/api/scan-prescription', methods=['POST'])
def scan_prescription():
    data       = request.get_json()
    image_data = data.get('image_data', '')
    if not image_data:
        return jsonify({'success': False, 'error': 'No image provided'}), 400
    if ',' in image_data:
        img_b64    = image_data.split(',')[1]
        media_type = image_data.split(';')[0].split(':')[1]
    else:
        img_b64    = image_data
        media_type = 'image/jpeg'
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{img_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": 'Read this prescription and return ONLY a JSON array: [{"name":"...","dosage":"...","timing":"Morning","total":30,"notes":""}]. Return [] if unreadable.'
                    }
                ]
            }],
            max_tokens=1024,
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace('```json','').replace('```','').strip()
        m   = _re.search(r'\[.*\]', raw, _re.DOTALL)
        if m: raw = m.group(0)
        medicines_found = json.loads(raw)
        u = get_username()
        medicines = load_medicines(u)
        added = []
        for med in medicines_found:
            if med.get('name') and med.get('dosage'):
                new_med = {
                    'name':          med['name'],
                    'dosage':        med['dosage'],
                    'timing':        med.get('timing', 'Morning'),
                    'total':         int(med.get('total', 30)),
                    'remaining':     int(med.get('total', 30)),
                    'taken_today':   False,
                    'notes':         med.get('notes', ''),
                    'reminder_time': '',
                    'photo':         ''
                }
                medicines.append(new_med)
                save_history(new_med['name'], 'Added via Scan', u)
                added.append(new_med)
        if added:
            save_medicines(medicines, u)
        return jsonify({
            'success':       True,
            'found':         len(added),
            'medicines':     added,
            'all_medicines': medicines
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── Drug Interaction Checker ───────────────────────────────────────────────────

@app.route('/api/check-interactions', methods=['POST'])
def check_interactions():
    medicines = load_medicines(get_viewing_username())
    if len(medicines) < 2:
        return jsonify({'success': True, 'has_interactions': False, 'interactions': [],
            'safe_message': f'You have {len(medicines)} medicine. Add at least 2 to check.'})
    med_list = ', '.join([m['name']+' ('+m['dosage']+')' for m in medicines])
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", temperature=0.1,
            messages=[
                {"role": "system", "content": 'Return ONLY raw JSON no markdown: {"has_interactions":true,"interactions":[{"medicines":["A","B"],"severity":"high","warning":"...","advice":"..."}],"safe_message":""}'},
                {"role": "user", "content": f"Check interactions for: {med_list}"}
            ]
        )
        raw    = response.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        m      = _re.search(r'\{.*\}', raw, _re.DOTALL)
        if m: raw = m.group(0)
        result = json.loads(raw)
        result.setdefault('has_interactions', False)
        result.setdefault('interactions', [])
        result.setdefault('safe_message', 'No dangerous interactions found. Consult your doctor.')
        return jsonify({'success': True, **result})
    except Exception:
        return jsonify({'success': True, 'has_interactions': False, 'interactions': [],
            'safe_message': 'Could not check automatically. Please consult your doctor.'})

# ── WhatsApp ───────────────────────────────────────────────────────────────────

@app.route('/api/whatsapp/daily-report', methods=['POST'])
def daily_report():
    u = get_username()
    medicines = load_medicines(u)
    try:
        send_daily_report(medicines, u)
        return jsonify({'success': True, 'message': 'Daily report sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/whatsapp/emergency', methods=['POST'])
def emergency():
    try:
        send_emergency(get_username())
        return jsonify({'success': True, 'message': 'Emergency alert sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/whatsapp/refill', methods=['POST'])
def refill_request():
    data          = request.get_json()
    medicine_name = data.get('medicine_name', '')
    remaining     = data.get('remaining', 0)
    try:
        send_refill_request(medicine_name, remaining, get_username())
        return jsonify({'success': True, 'message': 'Refill request sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/whatsapp/check-missed', methods=['POST'])
def check_missed():
    u = get_username()
    medicines    = load_medicines(u)
    current_hour = datetime.datetime.now().hour
    missed_meds  = []
    for med in medicines:
        if not med['taken_today'] and med['timing'] == 'Morning' and current_hour >= 11:
            try:
                send_missed_medicine(med['name'], med['timing'], u)
                save_history(med['name'], 'Missed', u)
                missed_meds.append(med['name'])
            except Exception:
                missed_meds.append(med['name'])
    return jsonify({'success': True, 'missed': missed_meds})

# ── Rewards ────────────────────────────────────────────────────────────────────

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
    return jsonify({'success': True, 'rewards': load_rewards(get_username()), 'badges': BADGES})

@app.route('/api/rewards/earn', methods=['POST'])
def earn_points():
    data    = request.get_json()
    reason  = data.get('reason', 'Medicine taken')
    pts     = int(data.get('points', 10))
    u       = get_username()
    rewards = load_rewards(u)
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
    if len(rewards['history']) == 1: award('first_dose')
    if rewards['streak'] >= 3:       award('streak_3')
    if rewards['streak'] >= 7:       award('streak_7')
    if rewards['streak'] >= 14:      award('streak_14')
    if rewards['streak'] >= 30:      award('streak_30')
    if rewards['points'] >= 50:      award('points_50')
    if rewards['points'] >= 100:     award('points_100')
    medicines = load_medicines(u)
    if medicines and all(m['taken_today'] for m in medicines):
        award('all_taken')
    save_rewards(rewards, u)
    return jsonify({'success': True, 'rewards': rewards, 'newly_earned': newly_earned})

@app.route('/api/rewards/reset', methods=['POST'])
def reset_rewards():
    save_rewards({'points': 0, 'streak': 0, 'last_date': '', 'badges': [], 'history': []}, get_username())
    return jsonify({'success': True})

# ── Appointments ───────────────────────────────────────────────────────────────

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    u     = get_username()
    appts = load_appointments(u)
    today = datetime.date.today()
    for a in appts:
        try:
            appt_date      = datetime.date.fromisoformat(a['date'])
            a['days_left'] = (appt_date - today).days
            a['status']    = 'today' if a['days_left'] == 0 else ('upcoming' if a['days_left'] > 0 else 'past')
        except Exception:
            a['days_left'] = None
            a['status']    = 'unknown'
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
    u     = get_username()
    appts = load_appointments(u)
    appts.append({'id': str(len(appts)+1)+'_'+datetime.datetime.now().strftime('%H%M%S'),
                  'doctor': doctor, 'hospital': hospital, 'date': date,
                  'time': time, 'notes': notes, 'reminded': False})
    appts.sort(key=lambda x: x['date'])
    save_appointments(appts, u)
    return jsonify({'success': True, 'appointments': appts}), 201

@app.route('/api/appointments/<appt_id>', methods=['DELETE'])
def delete_appointment(appt_id):
    u     = get_username()
    appts = [a for a in load_appointments(u) if a['id'] != appt_id]
    save_appointments(appts, u)
    return jsonify({'success': True, 'appointments': appts})

@app.route('/api/appointments/check-reminders', methods=['POST'])
def check_appointment_reminders():
    u       = get_username()
    appts   = load_appointments(u)
    today   = datetime.date.today()
    sent    = []
    updated = False
    for i, a in enumerate(appts):
        try:
            days_left = (datetime.date.fromisoformat(a['date']) - today).days
            if days_left == 1 and not a.get('reminded', False):
                from twilio.rest import Client
                client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
                from whatsapp import get_family_phones
                phones = get_family_phones(u)
                for phone in phones:
                    client.messages.create(
                        from_="whatsapp:+14155238886",
                        body=f"🏥 *MediBridge*\n\nAppointment TOMORROW!\n👨‍⚕️ Dr. {a['doctor']}\n🏥 {a.get('hospital','N/A')}\n🕐 {a.get('time','N/A')}",
                        to=phone
                    )
                appts[i]['reminded'] = True
                updated = True
                sent.append(a['doctor'])
        except Exception as e:
            print(f"Appt reminder error: {e}")
    if updated:
        save_appointments(appts, u)
    return jsonify({'success': True, 'sent': sent})

# ── Summary ────────────────────────────────────────────────────────────────────

@app.route('/api/summary', methods=['GET'])
def summary():
    u         = get_viewing_username()
    medicines = load_medicines(u)
    total     = len(medicines)
    taken     = sum(1 for m in medicines if m['taken_today'])
    missed    = total - taken
    low       = sum(1 for m in medicines if m['remaining'] <= 5)
    return jsonify({
        'success': True, 'total': total, 'taken': taken,
        'missed': missed, 'low_stock': low,
        'last_updated': datetime.datetime.now().strftime('%I:%M %p')
    })
# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')