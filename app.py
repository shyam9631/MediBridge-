import streamlit as st
from database import save_medicines, load_medicines, reset_daily_status, save_history, load_history, save_prescription, load_prescription, delete_medicine
import datetime
import json
import os

st.set_page_config(
    page_title="MediBridge",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    .block-container {
        max-width: 420px !important;
        padding: 0 !important;
        margin: 0 auto !important;
    }
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #0a0d1a 50%, #0a0a0f 100%);
    }
    .stButton > button {
        background: linear-gradient(135deg, #0099ff, #00d4ff, #0099ff) !important;
        background-size: 200% 200% !important;
        animation: gradientShift 3s ease infinite !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 14px !important;
        width: 100% !important;
        box-shadow: 0 4px 20px rgba(0,153,255,0.5) !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.5px !important;
    }
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 10px 30px rgba(0,153,255,0.7) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) scale(0.98) !important;
    }
    @keyframes gradientShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    @keyframes glowPulse {
        0% {box-shadow: 0 0 10px rgba(0,153,255,0.3);}
        50% {box-shadow: 0 0 25px rgba(0,153,255,0.7);}
        100% {box-shadow: 0 0 10px rgba(0,153,255,0.3);}
    }
    @keyframes fadeInUp {
        from {opacity: 0; transform: translateY(20px);}
        to {opacity: 1; transform: translateY(0);}
    }
    @keyframes float {
        0% {transform: translateY(0px);}
        50% {transform: translateY(-8px);}
        100% {transform: translateY(0px);}
    }
    .stTextInput > div > div > input {
        border-radius: 15px !important;
        border: 2px solid #0a1a2e !important;
        background-color: #0a0f1f !important;
        color: white !important;
        padding: 14px !important;
        font-size: 15px !important;
        transition: all 0.4s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border: 2px solid #0099ff !important;
        box-shadow: 0 0 20px rgba(0,153,255,0.4) !important;
        transform: scale(1.01) !important;
    }
    .stSelectbox > div > div {
        background-color: #0a0f1f !important;
        border-radius: 15px !important;
        border: 2px solid #0a1a2e !important;
        color: white !important;
        transition: all 0.3s ease !important;
    }
    .stNumberInput > div > div > input {
        background-color: #0a0f1f !important;
        border-radius: 15px !important;
        border: 2px solid #0a1a2e !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(135deg, #0a0f1f, #0a1a2e) !important;
        border-radius: 20px !important;
        padding: 5px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 15px !important;
        color: #666 !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0099ff, #00d4ff) !important;
        color: white !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,153,255,0.4) !important;
    }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #0a0f1f, #0a1a2e) !important;
        border-radius: 20px !important;
        padding: 15px !important;
        border: 1px solid #0a1a2e !important;
        animation: glowPulse 3s ease infinite !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px) !important;
        border-color: #0099ff !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #0a0f1f !important;
        border-radius: 15px !important;
        border: 2px solid #0a1a2e !important;
        color: white !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stForm"] {
        background: linear-gradient(135deg, #0a0f1f, #0a1a2e) !important;
        border-radius: 25px !important;
        padding: 25px !important;
        border: 1px solid #0a1a2e !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        animation: fadeInUp 0.5s ease !important;
    }
    hr {border-color: #0a1a2e !important;}
    .stSpinner > div {border-top-color: #0099ff !important;}
    </style>
""", unsafe_allow_html=True)

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def register_user(username, password, role, name):
    users = load_users()
    if username in users:
        return False, "Username already exists!"
    users[username] = {"password": password, "role": role, "name": name}
    save_users(users)
    return True, "Registered successfully!"

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, None, "Username not found!"
    if users[username]["password"] != password:
        return False, None, "Wrong password!"
    return True, users[username], "Login successful!"

if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user" not in st.session_state:
    st.session_state.user = None
if "medicines" not in st.session_state:
    st.session_state.medicines = reset_daily_status()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def show_logo():
    import base64
    
    logo_path = "Logo.jpeg"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
            <div style="text-align: center; padding: 20px 0 10px 0; animation: fadeInUp 0.6s ease;">
                <img src="data:image/jpeg;base64,{logo_data}" 
                    style="
                        width: 150px; 
                        height: 150px; 
                        border-radius: 50%;
                        object-fit: cover;
                        box-shadow: 0 8px 30px rgba(0,153,255,0.5);
                        border: 3px solid #0099ff;
                        animation: float 3s ease infinite;
                    "/>
                <p style="color: #555; font-size: 0.75em; letter-spacing: 2px; margin: 8px 0 0 0;">
                    CONNECTING HEALTHCARE SOLUTIONS
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align: center; padding: 20px 0 10px 0;">
                <div style="display: inline-block; background: linear-gradient(135deg, #0099ff, #00d4ff); border-radius: 20px; padding: 15px 20px;">
                    <span style="color: white; font-size: 2.5em;">💊</span>
                </div>
                <h1 style="background: linear-gradient(135deg, #0099ff, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 5px 0; font-size: 2em; font-weight: 800;">MediBridge</h1>
                <p style="color: #555; font-size: 0.75em; letter-spacing: 2px; margin: 0;">CONNECTING HEALTHCARE SOLUTIONS</p>
            </div>
        """, unsafe_allow_html=True)

def make_card(title, subtitle, emoji, color):
    return f"""
    <div style="background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 20px; padding: 20px; text-align: center; border: 1px solid #0a1a2e; margin-bottom: 10px; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <div style="font-size: 2.5em; animation: float 3s ease infinite;">{emoji}</div>
        <h3 style="color: white; margin: 8px 0 4px 0; font-size: 1em; font-weight: 700;">{title}</h3>
        <p style="color: #555; margin: 0; font-size: 0.8em;">{subtitle}</p>
    </div>
    """
def check_and_send_daily_report():
    import datetime
    now = datetime.datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # Send report at 10 PM every day
    if current_hour == 22 and current_minute == 0:
        medicines = st.session_state.medicines
        missed = [m for m in medicines if not m['taken_today']]
        
        if missed:
            try:
                from whatsapp import send_missed_daily_report
                send_missed_daily_report(medicines)
            except:
                pass

def landing_page():
    show_logo()
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 25px; padding: 25px; margin: 20px 0; border: 1px solid #0a1a2e; text-align: center; animation: fadeInUp 0.7s ease; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <h2 style="color: white; margin: 0 0 8px 0; font-size: 1.3em; font-weight: 700;">Welcome to MediBridge</h2>
            <p style="color: #555; margin: 0; font-size: 0.9em; line-height: 1.6;">Smart medicine tracking for senior citizens with real-time WhatsApp alerts for family</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👤 I am a...")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(make_card("Senior Citizen", "Track my medicines", "👴", "#0099ff"), unsafe_allow_html=True)
        if st.button("Select", key="senior_btn", use_container_width=True):
            st.session_state.selected_role = "senior"
            st.session_state.page = "auth"
            st.rerun()
    with col2:
        st.markdown(make_card("Family Member", "Monitor loved ones", "👨‍👩‍👧", "#00d4ff"), unsafe_allow_html=True)
        if st.button("Select", key="family_btn", use_container_width=True):
            st.session_state.selected_role = "family"
            st.session_state.page = "auth"
            st.rerun()

    st.markdown("""
        <div style="text-align: center; margin-top: 20px; animation: fadeInUp 1s ease;">
            <p style="color: #333; font-size: 0.75em;">Powered by AI • WhatsApp Notifications • Offline Mode</p>
        </div>
    """, unsafe_allow_html=True)

def auth_page():
    show_logo()
    role = st.session_state.get("selected_role", "senior")
    role_emoji = "👴" if role == "senior" else "👨‍👩‍👧"
    role_name = "Senior Citizen" if role == "senior" else "Family Member"

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0099ff20, #00d4ff10); border-radius: 20px; padding: 20px; text-align: center; border: 1px solid #0099ff50; margin-bottom: 25px; animation: fadeInUp 0.5s ease; box-shadow: 0 8px 25px rgba(0,153,255,0.2);">
            <div style="font-size: 3em; animation: float 3s ease infinite;">{role_emoji}</div>
            <h2 style="background: linear-gradient(135deg, #0099ff, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 10px 0 5px 0; font-weight: 800;">{role_name}</h2>
            <p style="color: #555; margin: 0; font-size: 0.85em;">Welcome to MediBridge!</p>
        </div>
    """, unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.auth_mode = "login"
    with col2:
        if st.button("📝 Register", use_container_width=True):
            st.session_state.auth_mode = "register"

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        st.markdown("""
            <div style="text-align: center; margin-bottom: 20px; animation: fadeInUp 0.6s ease;">
                <h2 style="color: white; margin: 0; font-size: 1.5em; font-weight: 700;">Welcome Back! 👋</h2>
                <p style="color: #555; margin: 5px 0 0 0; font-size: 0.85em;">Login to continue</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            login_btn = st.form_submit_button("🚀 Login to MediBridge", use_container_width=True)
            if login_btn:
                if username and password:
                    success, user_data, msg = login_user(username, password)
                    if success:
                        if user_data["role"] != role:
                            st.error(f"❌ Wrong role! This account is for {user_data['role']}!")
                        else:
                            st.session_state.user = {"username": username, "name": user_data["name"], "role": user_data["role"]}
                            st.session_state.page = "dashboard"
                            st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.error("❌ Please fill all fields!")
        st.markdown("""
            <div style="text-align: center; margin-top: 15px;">
                <p style="color: #333; font-size: 0.8em;">Don't have an account? Click Register above!</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 20px; animation: fadeInUp 0.6s ease;">
                <h2 style="color: white; margin: 0; font-size: 1.5em; font-weight: 700;">Create Account! ✨</h2>
                <p style="color: #555; margin: 5px 0 0 0; font-size: 0.85em;">Join MediBridge today</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("register_form"):
            name = st.text_input("😊 Your Full Name")
            username = st.text_input("👤 Choose Username")
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("🔒 Password", type="password")
            with col2:
                confirm = st.text_input("🔒 Confirm", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            register_btn = st.form_submit_button("✨ Create My Account", use_container_width=True)
            if register_btn:
                if name and username and password and confirm:
                    if password != confirm:
                        st.error("❌ Passwords don't match!")
                    elif len(password) < 4:
                        st.error("❌ Password too short!")
                    else:
                        success, msg = register_user(username, password, role, name)
                        if success:
                            st.success("✅ Account created! Please login!")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.error("❌ Fill all fields!")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Go Back", use_container_width=True):
        st.session_state.page = "landing"
        st.rerun()

def make_medicine_card(med, index):
    border = "#2ECC71" if med["taken_today"] else "#0099ff"
    status = "✅ Taken" if med["taken_today"] else "⏳ Pending"
    status_color = "#2ECC71" if med["taken_today"] else "#0099ff"
    notes_part = ""
    if med.get("notes"):
        notes_part = "<p style=\"color: #555; margin: 4px 0; font-size: 0.75em;\">📝 " + str(med["notes"]) + "</p>"
    html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 20px; padding: 18px; border: 1px solid #0a1a2e; border-left: 4px solid " + border + "; margin-bottom: 14px; box-shadow: 0 8px 25px rgba(0,0,0,0.3); transition: all 0.3s ease;\">"
    html += "<div style=\"display: flex; justify-content: space-between; align-items: center;\">"
    html += "<div>"
    html += "<h3 style=\"color: white; margin: 0; font-size: 1.05em; font-weight: 700;\">💊 " + str(med["name"]) + "</h3>"
    html += "<p style=\"color: #777; margin: 5px 0; font-size: 0.85em;\">" + str(med["dosage"]) + " • ⏰ " + str(med["timing"]) + "</p>"
    html += "<p style=\"color: #E74C3C; margin: 4px 0; font-size: 0.8em; font-weight: 700;\">📦 " + str(med["remaining"]) + " tablets left</p>"
    html += notes_part
    html += "</div>"
    html += "<div style=\"background: linear-gradient(135deg, " + status_color + "30, " + status_color + "10); padding: 8px 14px; border-radius: 20px; border: 1px solid " + status_color + "50;\">"
    html += "<p style=\"color: " + status_color + "; margin: 0; font-size: 0.75em; font-weight: 700;\">" + status + "</p>"
    html += "</div></div></div>"
    st.markdown(html, unsafe_allow_html=True)

def senior_dashboard():
    check_and_send_daily_report()
    user = st.session_state.user
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0099ff, #00d4ff); padding: 15px 20px; border-radius: 0 0 25px 25px; margin-bottom: 20px; box-shadow: 0 8px 25px rgba(0,153,255,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.75em;">Good day! 👋</p>
                    <h2 style="color: white; margin: 2px 0; font-size: 1.2em; font-weight: 700;">{user['name']}</h2>
                </div>
                <div style="text-align: right;">
                    <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.75em;">💊 MediBridge</p>
                    <p style="color: white; margin: 0; font-size: 0.8em; font-weight: 600;">Senior Citizen 👴</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    total = len(st.session_state.medicines)
    taken = sum(1 for m in st.session_state.medicines if m["taken_today"])
    remaining = total - taken

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💊 Total", total)
    with col2:
        st.metric("✅ Taken", taken)
    with col3:
        st.metric("⏳ Left", remaining)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💊 Medicines", "📋 Prescription", "📊 History", "🤖 MediBot", "⚙️ Settings"])

    with tab1:
        st.markdown("### ➕ Add Medicine")
        with st.form("add_form"):
            med_name = st.text_input("💊 Medicine Name")
            col1, col2 = st.columns(2)
            with col1:
                dosage = st.text_input("📏 Dosage")
            with col2:
                total_count = st.number_input("📦 Tablets", min_value=1, max_value=500, value=30)
            timing = st.selectbox("⏰ Timing", [
                "Morning", "Afternoon", "Evening", "Night",
                "Morning & Night", "Morning, Afternoon & Night",
                "After Food", "Before Food"
            ])
            notes = st.text_input("📝 Notes (optional)")
            add_btn = st.form_submit_button("➕ Add Medicine", use_container_width=True)
            if add_btn:
                if med_name and dosage:
                    st.session_state.medicines.append({
                        "name": med_name, "dosage": dosage, "timing": timing,
                        "total": total_count, "remaining": total_count,
                        "taken_today": False, "notes": notes
                    })
                    save_medicines(st.session_state.medicines)
                    save_history(med_name, "Added")
                    st.success(f"✅ {med_name} added!")
                    st.rerun()
                else:
                    st.error("❌ Fill Medicine Name and Dosage!")

        st.markdown("### 📋 Today's Medicines")
        if len(st.session_state.medicines) == 0:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 20px; padding: 30px; text-align: center; border: 1px solid #0a1a2e;">
                    <p style="font-size: 2em; margin: 0;">💊</p>
                    <h3 style="color: #444; margin: 10px 0 5px 0;">No medicines yet</h3>
                    <p style="color: #333; margin: 0; font-size: 0.85em;">Add your first medicine above</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            for i, med in enumerate(st.session_state.medicines):
                make_medicine_card(med, i)
                if not med["taken_today"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button("✅ Took it!", key=f"took_{i}", use_container_width=True):
                            st.session_state.medicines[i]["taken_today"] = True
                            st.session_state.medicines[i]["remaining"] -= 1
                            save_medicines(st.session_state.medicines)
                            save_history(med['name'], "Taken")
                            try:
                                from whatsapp import send_medicine_taken, send_low_stock_alert
                                send_medicine_taken(med['name'], med['dosage'], st.session_state.medicines[i]["remaining"])
                                st.success("✅ Done! Family notified on WhatsApp! 📱")
                            except:
                                st.success("✅ Medicine marked as taken!")
                            if st.session_state.medicines[i]["remaining"] <= 5:
                                try:
                                    send_low_stock_alert(med['name'], st.session_state.medicines[i]["remaining"])
                                except:
                                    pass
                                st.warning("⚠️ Low stock! Family alerted!")
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                            save_history(med['name'], "Deleted")
                            st.session_state.medicines = delete_medicine(i)
                            st.rerun()
                if med["remaining"] <= 5:
                    st.warning(f"⚠️ Only {med['remaining']} left!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Check Missed Medicines", use_container_width=True):
            current_hour = datetime.datetime.now().hour
            missed_any = False
            for med in st.session_state.medicines:
                if not med["taken_today"]:
                    if med["timing"] == "Morning" and current_hour >= 11:
                        try:
                            from whatsapp import send_missed_medicine
                            send_missed_medicine(med['name'], med['timing'])
                            save_history(med['name'], "Missed")
                        except:
                            pass
                        st.error(f"❌ {med['name']} missed!")
                        missed_any = True
            if not missed_any:
                st.success("✅ All medicines on track!")

    with tab2:
        st.markdown("### 📋 Prescription")
        saved = load_prescription()
        if saved:
            html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 20px; padding: 20px; border: 1px solid #0a1a2e; border-left: 4px solid #0099ff; margin-bottom: 20px;\">"
            html += "<h3 style=\"color: white; margin: 0 0 10px 0;\">👴 " + str(saved['patient_name']) + "</h3>"
            html += "<p style=\"color: #888; margin: 5px 0;\">👨‍⚕️ Dr. " + str(saved['doctor_name']) + "</p>"
            html += "<p style=\"color: #888; margin: 5px 0;\">🏥 " + str(saved.get('hospital_name', 'N/A')) + "</p>"
            html += "<p style=\"color: #888; margin: 5px 0;\">📅 " + str(saved['date']) + "</p>"
            html += "<p style=\"color: #888; margin: 5px 0;\">📅 Next: " + str(saved.get('next_visit', 'N/A')) + "</p>"
            html += "<p style=\"color: white; margin: 10px 0 0 0;\">📝 " + str(saved.get('notes', 'None')) + "</p>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        with st.form("prescription_form"):
            name = st.text_input("👴 Patient Name")
            col1, col2 = st.columns(2)
            with col1:
                doctor = st.text_input("👨‍⚕️ Doctor Name")
            with col2:
                hospital = st.text_input("🏥 Hospital")
            col3, col4 = st.columns(2)
            with col3:
                date = st.date_input("📅 Date")
            with col4:
                next_visit = st.date_input("📅 Next Visit")
            contact = st.text_input("📞 Doctor Contact")
            notes_rx = st.text_area("📝 Doctor Notes")
            save_btn = st.form_submit_button("💾 Save Prescription", use_container_width=True)
            if save_btn:
                if name and doctor:
                    save_prescription({"patient_name": name, "doctor_name": doctor, "hospital_name": hospital, "date": str(date), "next_visit": str(next_visit), "contact": contact, "notes": notes_rx})
                    st.success("✅ Prescription saved!")
                    st.rerun()
                else:
                    st.error("❌ Fill patient and doctor name!")

    with tab3:
        st.markdown("### 📊 Medicine History")
        history = load_history()
        if len(history) == 0:
            st.info("No history yet!")
        else:
            taken_c = sum(1 for h in history if h["action"] == "Taken")
            missed_c = sum(1 for h in history if h["action"] == "Missed")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("✅ Total Taken", taken_c)
            with col2:
                st.metric("❌ Total Missed", missed_c)
            st.markdown("<br>", unsafe_allow_html=True)
            for record in reversed(history):
                if record["action"] == "Taken":
                    color, icon = "#2ECC71", "✅"
                elif record["action"] == "Missed":
                    color, icon = "#E74C3C", "❌"
                elif record["action"] == "Deleted":
                    color, icon = "#E74C3C", "🗑️"
                else:
                    color, icon = "#0099ff", "➕"
                html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); padding: 12px 15px; border-radius: 15px; border-left: 3px solid " + color + "; margin-bottom: 8px;\">"
                html += "<p style=\"color: white; margin: 0; font-size: 0.9em; font-weight: 600;\">" + icon + " " + str(record['medicine']) + " — " + str(record['action']) + "</p>"
                html += "<p style=\"color: #555; margin: 3px 0 0 0; font-size: 0.75em;\">🕐 " + str(record['time']) + "</p>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
            if st.button("🗑️ Clear History", use_container_width=True):
                with open("history.json", "w") as f:
                    json.dump([], f)
                st.success("Cleared!")
                st.rerun()

    with tab4:
        st.markdown("### 🤖 MediBot")
        st.markdown("""
            <div style="background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 15px; padding: 12px 15px; border-left: 3px solid #0099ff; margin-bottom: 15px;">
                <p style="color: #888; margin: 0; font-size: 0.85em;">🤖 Hi! Ask me anything about your medicines! 💊</p>
            </div>
        """, unsafe_allow_html=True)

        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                html = "<div style=\"background: linear-gradient(135deg, #0099ff, #00d4ff); padding: 10px 14px; border-radius: 18px 18px 4px 18px; margin: 6px 0 6px 20%; text-align: right;\">"
                html += "<p style=\"color: white; margin: 0; font-size: 0.85em;\">" + str(chat['message']) + "</p></div>"
            else:
                html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); padding: 10px 14px; border-radius: 18px 18px 18px 4px; margin: 6px 20% 6px 0; border: 1px solid #0a1a2e;\">"
                html += "<p style=\"color: white; margin: 0; font-size: 0.85em;\">🤖 " + str(chat['message']) + "</p></div>"
            st.markdown(html, unsafe_allow_html=True)

        st.markdown("**Quick Questions:**")
        qc1, qc2 = st.columns(2)
        with qc1:
            if st.button("💊 My medicines?", use_container_width=True):
                st.session_state.quick_q = "What medicines am I taking and what are they for?"
            if st.button("⚠️ Side effects?", use_container_width=True):
                st.session_state.quick_q = "What are the side effects of my medicines?"
        with qc2:
            if st.button("⏰ When to take?", use_container_width=True):
                st.session_state.quick_q = "When exactly should I take each medicine?"
            if st.button("📦 Stock check?", use_container_width=True):
                st.session_state.quick_q = "Which medicines are running low?"

        user_input = st.text_input("💬 Ask MediBot:", value=st.session_state.get("quick_q", ""), placeholder="e.g. Can I take this with food?")
        col1, col2 = st.columns([4, 1])
        with col1:
            send = st.button("📤 Send", use_container_width=True)
        with col2:
            if st.button("🗑️", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        if send and user_input:
            st.session_state.chat_history.append({"role": "user", "message": user_input})
            with st.spinner("MediBot thinking... 🤔"):
                try:
                    from chatbot import get_medicine_response
                    response = get_medicine_response(user_input, st.session_state.medicines)
                except:
                    response = "Sorry, having trouble connecting. Try again! 🙏"
            st.session_state.chat_history.append({"role": "bot", "message": response})
            if "quick_q" in st.session_state:
                del st.session_state.quick_q
            st.rerun()

    with tab5:
        st.markdown("### ⚙️ Settings")
        html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 20px; padding: 20px; border: 1px solid #0a1a2e; margin-bottom: 15px;\">"
        html += "<h3 style=\"color: white; margin: 0 0 10px 0;\">👤 My Profile</h3>"
        html += "<p style=\"color: #888; margin: 5px 0;\">Name: " + str(user['name']) + "</p>"
        html += "<p style=\"color: #888; margin: 5px 0;\">Username: " + str(user['username']) + "</p>"
        html += "<p style=\"color: #888; margin: 5px 0;\">Role: Senior Citizen 👴</p>"
        html += "<p style=\"color: #888; margin: 5px 0;\">Date: " + str(datetime.date.today()) + "</p>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("### 📱 Send Alerts")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Daily Report", use_container_width=True):
                try:
                    from whatsapp import send_daily_report
                    send_daily_report(st.session_state.medicines)
                    st.success("✅ Report sent!")
                except:
                    st.error("❌ Rejoin WhatsApp sandbox!")
        with col2:
            if st.button("🆘 Emergency!", use_container_width=True):
                try:
                    from twilio.rest import Client
                    from dotenv import load_dotenv
                    load_dotenv()
                    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
                    client.messages.create(
                        from_="whatsapp:+14155238886",
                        body="🚨 *EMERGENCY ALERT*\n\nYour loved one needs immediate help!\n\nPlease call or visit them right away!\n\n_Sent by MediBridge_ 🏥",
                        to=os.getenv("FAMILY_PHONE")
                    )
                    st.success("🆘 Emergency alert sent!")
                except:
                    st.error("❌ Rejoin WhatsApp sandbox!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "landing"
            st.rerun()

def family_dashboard():
    user = st.session_state.user
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0099ff, #00d4ff); padding: 15px 20px; border-radius: 0 0 25px 25px; margin-bottom: 20px; box-shadow: 0 8px 25px rgba(0,153,255,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.75em;">Monitoring 👀</p>
                    <h2 style="color: white; margin: 2px 0; font-size: 1.2em; font-weight: 700;">{user['name']}</h2>
                </div>
                <div style="text-align: right;">
                    <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.75em;">💊 MediBridge</p>
                    <p style="color: white; margin: 0; font-size: 0.8em; font-weight: 600;">Family Member 👨‍👩‍👧</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    total = len(st.session_state.medicines)
    taken = sum(1 for m in st.session_state.medicines if m["taken_today"])
    missed = total - taken
    low = sum(1 for m in st.session_state.medicines if m["remaining"] <= 5)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💊", total)
    with col2:
        st.metric("✅", taken)
    with col3:
        st.metric("❌", missed)
    with col4:
        st.metric("⚠️", low)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📊 Status", "📋 Prescription", "📝 History"])               

    with tab1:
        st.markdown("### 📊 Medicine Status")
        if len(st.session_state.medicines) == 0:
            st.warning("No medicines added yet!")
        else:
            for med in st.session_state.medicines:
                border = "#2ECC71" if med["taken_today"] else "#E74C3C"
                status = "✅ Taken!" if med["taken_today"] else "❌ Not taken!"
                status_color = "#2ECC71" if med["taken_today"] else "#E74C3C"
                html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 20px; padding: 16px; border: 1px solid #0a1a2e; border-left: 4px solid " + border + "; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);\">"
                html += "<div style=\"display: flex; justify-content: space-between; align-items: center;\">"
                html += "<div>"
                html += "<h3 style=\"color: white; margin: 0; font-size: 1em; font-weight: 700;\">💊 " + str(med['name']) + "</h3>"
                html += "<p style=\"color: #888; margin: 4px 0; font-size: 0.85em;\">" + str(med['dosage']) + " • " + str(med['timing']) + "</p>"
                html += "<p style=\"color: #E74C3C; margin: 4px 0; font-size: 0.8em;\">📦 " + str(med['remaining']) + " left</p>"
                html += "</div>"
                html += "<div style=\"background: " + status_color + "20; padding: 8px 12px; border-radius: 15px; border: 1px solid " + status_color + "40;\">"
                html += "<p style=\"color: " + status_color + "; margin: 0; font-weight: 700; font-size: 0.8em;\">" + status + "</p>"
                html += "</div></div>"
                if med['remaining'] <= 5:
                    html += "<p style=\"color: #E74C3C; margin: 8px 0 0 0; font-size: 0.8em;\">⚠️ Low stock! Only " + str(med['remaining']) + " left!</p>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

    with tab2:
        st.markdown("### 📋 Prescription")
        saved = load_prescription()
        if saved:
            html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); border-radius: 20px; padding: 20px; border: 1px solid #0a1a2e; border-left: 4px solid #0099ff;\">"
            html += "<h3 style=\"color: white; margin: 0 0 10px 0;\">👴 " + str(saved['patient_name']) + "</h3>"
            html += "<p style=\"color: #888; margin: 5px 0;\">👨‍⚕️ Dr. " + str(saved['doctor_name']) + "</p>"
            html += "<p style=\"color: #888; margin: 5px 0;\">🏥 " + str(saved.get('hospital_name', 'N/A')) + "</p>"
            html += "<p style=\"color: #888; margin: 5px 0;\">📅 " + str(saved['date']) + "</p>"
            html += "<p style=\"color: #888; margin: 5px 0;\">📅 Next: " + str(saved.get('next_visit', 'N/A')) + "</p>"
            html += "<p style=\"color: white; margin: 10px 0 0 0;\">📝 " + str(saved.get('notes', 'None')) + "</p>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("No prescription saved yet!")

    with tab3:
        st.markdown("### 📝 Recent Activity")
        history = load_history()
        if not history:
            st.info("No activity yet!")
        else:
            for record in reversed(history[-15:]):
                if record["action"] == "Taken":
                    color, icon = "#2ECC71", "✅"
                elif record["action"] == "Missed":
                    color, icon = "#E74C3C", "❌"
                else:
                    color, icon = "#0099ff", "➕"
                html = "<div style=\"background: linear-gradient(135deg, #0a0f1f, #0a1a2e); padding: 10px 14px; border-radius: 12px; border-left: 3px solid " + color + "; margin-bottom: 8px;\">"
                html += "<p style=\"color: white; margin: 0; font-size: 0.85em; font-weight: 600;\">" + icon + " " + str(record['medicine']) + " — " + str(record['action']) + "</p>"
                html += "<p style=\"color: #444; margin: 2px 0 0 0; font-size: 0.75em;\">🕐 " + str(record['time']) + "</p>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.page = "landing"
        st.rerun()

if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "auth":
    auth_page()
elif st.session_state.page == "dashboard":
    if st.session_state.user:
        if st.session_state.user["role"] == "senior":
            senior_dashboard()
        else:
            family_dashboard()
    else:
        st.session_state.page = "landing"
        st.rerun()