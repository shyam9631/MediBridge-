import streamlit as st
from whatsapp import send_medicine_taken, send_low_stock_alert, send_missed_medicine
from database import save_medicines, load_medicines, reset_daily_status, save_history, load_history
import datetime

# Page Configuration
st.set_page_config(
    page_title="MediBridge",
    page_icon="💊",
    layout="centered"
)

# Custom CSS Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    h1 {
        color: #ffffff;
        text-align: center;
    }
    .stButton > button {
        background-color: #3498DB;
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #2980B9;
        transform: scale(1.05);
    }
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #667eea;
        background-color: #1e2130;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Beautiful Header
st.markdown("""
    <div style='text-align: center; padding: 20px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 15px; margin-bottom: 20px;'>
        <h1 style='color: white; font-size: 3em;'>
            💊 MediBridge
        </h1>
        <p style='color: white; font-size: 1.2em;'>
            Smart Medicine Tracker for Your Loved Ones
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# Load medicines from database on startup
if "medicines" not in st.session_state:
    st.session_state.medicines = reset_daily_status()

# Login Selection
st.markdown("### Who are you?")
col1, col2 = st.columns(2)

with col1:
    if st.button("👴 I am a Senior Citizen", use_container_width=True):
        st.session_state.user_type = "senior"

with col2:
    if st.button("👨‍👩‍👧 I am a Family Member", use_container_width=True):
        st.session_state.user_type = "family"

# Show based on selection
if "user_type" in st.session_state:
    st.divider()

    # =====================
    # SENIOR CITIZEN DASHBOARD
    # =====================
    if st.session_state.user_type == "senior":
        st.markdown("## 👴 Senior Citizen Dashboard")

        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["💊 Medicines", "📋 Prescription", "📊 History", "🤖 MediBot"])

        # =====================
        # TAB 1 - MEDICINES
        # =====================
        with tab1:
            # Add Medicine Form
            st.markdown("### ➕ Add New Medicine")
            with st.form("add_medicine_form"):
                med_name = st.text_input("💊 Medicine Name")
                dosage = st.text_input("📏 Dosage (e.g. 500mg)")
                timing = st.selectbox("⏰ Timing", [
                    "Morning", "Afternoon", "Evening", "Night",
                    "Morning & Night", "Morning, Afternoon & Night"
                ])
                total_count = st.number_input(
                    "📦 Total Tablets/Capsules",
                    min_value=1,
                    max_value=500,
                    value=30
                )
                submitted = st.form_submit_button(
                    "➕ Add Medicine",
                    use_container_width=True
                )

                if submitted:
                    if med_name and dosage:
                        st.session_state.medicines.append({
                            "name": med_name,
                            "dosage": dosage,
                            "timing": timing,
                            "total": total_count,
                            "remaining": total_count,
                            "taken_today": False
                        })
                        # Save to database
                        save_medicines(st.session_state.medicines)
                        # Save to history
                        save_history(med_name, "Added")
                        st.success(f"✅ {med_name} added successfully!")
                    else:
                        st.error("❌ Please fill all fields!")

            # Show Medicine List
            st.markdown("### 📋 Your Medicines Today")
            if len(st.session_state.medicines) == 0:
                st.info("No medicines added yet. Add your first medicine above!")
            else:
                for i, med in enumerate(st.session_state.medicines):
                    st.markdown(f"""
                        <div style='
                            background: #1e2130;
                            padding: 15px;
                            border-radius: 12px;
                            border-left: 5px solid {"#2ECC71" if med["taken_today"] else "#3498DB"};
                            box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
                            margin-bottom: 10px;'>
                            <h3 style='color: white;'>
                                💊 {med['name']} — {med['dosage']}
                            </h3>
                            <p style='color: #aaaaaa;'>⏰ {med['timing']}</p>
                            <p style='color: #E74C3C; font-weight: bold;'>
                                📦 Remaining: {med['remaining']} tablets
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if not med["taken_today"]:
                            if st.button(f"✅ Took it!", key=f"took_{i}", use_container_width=True):
                                st.session_state.medicines[i]["taken_today"] = True
                                st.session_state.medicines[i]["remaining"] -= 1

                                # Save to database
                                save_medicines(st.session_state.medicines)

                                # Save to history
                                save_history(med['name'], "Taken")

                                # Send WhatsApp notification
                                try:
                                    send_medicine_taken(
                                        med['name'],
                                        med['dosage'],
                                        st.session_state.medicines[i]["remaining"]
                                    )
                                    st.success(f"✅ {med['name']} taken! Family notified on WhatsApp! 📱")
                                except:
                                    st.success(f"✅ {med['name']} marked as taken!")

                                # Low stock WhatsApp alert
                                if st.session_state.medicines[i]["remaining"] <= 5:
                                    try:
                                        send_low_stock_alert(
                                            med['name'],
                                            st.session_state.medicines[i]["remaining"]
                                        )
                                        st.warning(f"⚠️ Low stock alert sent to family!")
                                    except:
                                        st.warning(f"⚠️ Only {med['remaining']} tablets left!")

                                st.rerun()
                        else:
                            st.success("✅ Taken!")

                    if med["remaining"] <= 5:
                        st.warning(f"⚠️ Low Stock! Only {med['remaining']} tablets left!")
                    st.divider()

            # Check missed medicines button
            st.markdown("### ⚠️ Check Missed Medicines")
            if st.button("🔍 Check Now", use_container_width=True):
                current_hour = datetime.datetime.now().hour
                missed_any = False
                for med in st.session_state.medicines:
                    if not med["taken_today"]:
                        if med["timing"] == "Morning" and current_hour >= 11:
                            try:
                                send_missed_medicine(med['name'], med['timing'])
                                save_history(med['name'], "Missed")
                            except:
                                pass
                            st.error(f"❌ {med['name']} was missed! Family notified!")
                            missed_any = True
                        elif med["timing"] == "Night" and current_hour >= 23:
                            try:
                                send_missed_medicine(med['name'], med['timing'])
                                save_history(med['name'], "Missed")
                            except:
                                pass
                            st.error(f"❌ {med['name']} was missed! Family notified!")
                            missed_any = True
                if not missed_any:
                    st.success("✅ No missed medicines!")

        # =====================
        # TAB 2 - PRESCRIPTION
        # =====================
        with tab2:
            st.markdown("### 📋 Add Prescription Details")
            with st.form("prescription_form"):
                patient_name = st.text_input("👴 Patient Name")
                doctor_name = st.text_input("👨‍⚕️ Doctor Name")
                hospital_name = st.text_input("🏥 Hospital Name")
                date = st.date_input("📅 Prescription Date")
                notes = st.text_area("📝 Doctor Notes")
                prescription_submitted = st.form_submit_button(
                    "💾 Save Prescription",
                    use_container_width=True
                )

                if prescription_submitted:
                    if patient_name and doctor_name:
                        st.session_state.prescription = {
                            "patient_name": patient_name,
                            "doctor_name": doctor_name,
                            "hospital_name": hospital_name,
                            "date": str(date),
                            "notes": notes
                        }
                        st.success("✅ Prescription saved successfully!")
                    else:
                        st.error("❌ Please fill patient and doctor name!")

            # Show saved prescription
            if "prescription" in st.session_state:
                st.markdown("### 📄 Current Prescription")
                p = st.session_state.prescription
                st.markdown(f"""
                    <div style='
                        background: #1e2130;
                        padding: 20px;
                        border-radius: 12px;
                        border-left: 5px solid #667eea;'>
                        <h3 style='color: white;'>👴 {p['patient_name']}</h3>
                        <p style='color: #aaaaaa;'>👨‍⚕️ Dr. {p['doctor_name']}</p>
                        <p style='color: #aaaaaa;'>🏥 {p['hospital_name']}</p>
                        <p style='color: #aaaaaa;'>📅 {p['date']}</p>
                        <p style='color: white;'>📝 {p['notes']}</p>
                    </div>
                """, unsafe_allow_html=True)

        # =====================
        # TAB 3 - HISTORY
        # =====================
        with tab3:
            st.markdown("### 📊 Medicine History")
            history = load_history()
            if len(history) == 0:
                st.info("No history yet!")
            else:
                for record in reversed(history):
                    color = "#2ECC71" if record["action"] == "Taken" else "#E74C3C" if record["action"] == "Missed" else "#3498DB"
                    icon = "✅" if record["action"] == "Taken" else "❌" if record["action"] == "Missed" else "➕"
                    st.markdown(f"""
                        <div style='
                            background: #1e2130;
                            padding: 10px 15px;
                            border-radius: 10px;
                            border-left: 4px solid {color};
                            margin-bottom: 8px;'>
                            <p style='color: white; margin: 0;'>
                                {icon} <b>{record['medicine']}</b> — {record['action']}
                            </p>
                            <p style='color: #aaaaaa; margin: 0; font-size: 0.8em;'>
                                🕐 {record['time']}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
        # =====================
        # TAB 4 - AI CHATBOT
        # =====================
        with tab4:
            st.markdown("### 🤖 MediBot — Your Medicine Assistant")
            st.info("Ask me anything about your medicines!")

            # Chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            # Show chat history
            for chat in st.session_state.chat_history:
                if chat["role"] == "user":
                    st.markdown(f"""
                        <div style='
                            background: #2C3E50;
                            padding: 10px 15px;
                            border-radius: 10px;
                            margin-bottom: 8px;
                            text-align: right;'>
                            <p style='color: white; margin: 0;'>
                                👴 {chat['message']}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style='
                            background: #1e2130;
                            padding: 10px 15px;
                            border-radius: 10px;
                            border-left: 4px solid #667eea;
                            margin-bottom: 8px;'>
                            <p style='color: white; margin: 0;'>
                                🤖 {chat['message']}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

            # Quick question buttons
            st.markdown("#### Quick Questions:")
            qcol1, qcol2 = st.columns(2)
            with qcol1:
                if st.button("💊 What are my medicines?", use_container_width=True):
                    st.session_state.quick_question = "What medicines am I taking?"
            with qcol2:
                if st.button("⏰ When to take medicines?", use_container_width=True):
                    st.session_state.quick_question = "When should I take my medicines?"

            qcol3, qcol4 = st.columns(2)
            with qcol3:
                if st.button("⚠️ Side effects?", use_container_width=True):
                    st.session_state.quick_question = "What are the side effects of my medicines?"
            with qcol4:
                if st.button("📦 Stock status?", use_container_width=True):
                    st.session_state.quick_question = "How many medicines do I have left?"

            # User input
            user_input = st.text_input(
                "💬 Ask MediBot anything:",
                value=st.session_state.get("quick_question", ""),
                placeholder="e.g. What is Paracetamol for?"
            )

            if st.button("📤 Send", use_container_width=True):
                if user_input:
                    st.session_state.chat_history.append({
                        "role": "user",
                        "message": user_input
                    })

                    with st.spinner("MediBot is thinking... 🤔"):
                        try:
                            from chatbot import get_medicine_response
                            response = get_medicine_response(
                                user_input,
                                st.session_state.medicines
                            )
                        except Exception as e:
                            response = f"Sorry, I am having trouble connecting. Error: {str(e)}"

                    st.session_state.chat_history.append({
                        "role": "bot",
                        "message": response
                    })

                    if "quick_question" in st.session_state:
                        del st.session_state.quick_question

                    st.rerun()

            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    # =====================
    # FAMILY DASHBOARD
    # =====================
    elif st.session_state.user_type == "family":
        st.markdown("## 👨‍👩‍👧 Family Dashboard")
        st.info("👀 Monitoring your loved one's medicines")

        # Overview stats
        if len(st.session_state.medicines) > 0:
            total = len(st.session_state.medicines)
            taken = sum(1 for m in st.session_state.medicines if m["taken_today"])
            missed = total - taken

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💊 Total", total)
            with col2:
                st.metric("✅ Taken", taken)
            with col3:
                st.metric("❌ Remaining", missed)

        st.divider()

        if len(st.session_state.medicines) == 0:
            st.warning("No medicines added yet by senior citizen!")
        else:
            st.markdown("### 📊 Medicine Status")
            for med in st.session_state.medicines:
                st.markdown(f"""
                    <div style='
                        background: #1e2130;
                        padding: 15px;
                        border-radius: 12px;
                        border-left: 5px solid {"#2ECC71" if med["taken_today"] else "#E74C3C"};
                        box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
                        margin-bottom: 10px;'>
                        <h3 style='color: white;'>
                            💊 {med['name']} — {med['dosage']}
                        </h3>
                        <p style='color: #aaaaaa;'>⏰ {med['timing']}</p>
                        <p style='color: {"#2ECC71" if med["taken_today"] else "#E74C3C"};
                        font-weight: bold; font-size: 1.2em;'>
                            {"✅ Medicine Taken!" if med["taken_today"] else "❌ Not Taken Yet!"}
                        </p>
                        <p style='color: #aaaaaa;'>
                            📦 Remaining: {med['remaining']} tablets
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                if med["remaining"] <= 5:
                    st.warning(f"⚠️ {med['name']} running low! Only {med['remaining']} left!")
                st.divider()

        # History section for family
        st.markdown("### 📊 Recent Activity")
        history = load_history()
        if len(history) == 0:
            st.info("No activity yet!")
        else:
            for record in reversed(history[-5:]):
                color = "#2ECC71" if record["action"] == "Taken" else "#E74C3C" if record["action"] == "Missed" else "#3498DB"
                icon = "✅" if record["action"] == "Taken" else "❌" if record["action"] == "Missed" else "➕"
                st.markdown(f"""
                    <div style='
                        background: #1e2130;
                        padding: 10px 15px;
                        border-radius: 10px;
                        border-left: 4px solid {color};
                        margin-bottom: 8px;'>
                        <p style='color: white; margin: 0;'>
                            {icon} <b>{record['medicine']}</b> — {record['action']}
                        </p>
                        <p style='color: #aaaaaa; margin: 0; font-size: 0.8em;'>
                            🕐 {record['time']}
                        </p>
                    </div>
                """, unsafe_allow_html=True)