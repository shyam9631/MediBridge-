import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="MediBridge",
    page_icon="💊",
    layout="centered"
)

# Main Title
st.title("💊 MediBridge")
st.subheader("Smart Medicine Tracker for Your Loved Ones")
st.divider()

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
                    # Save medicine to session
                    if "medicines" not in st.session_state:
                        st.session_state.medicines = []
                    st.session_state.medicines.append({
                        "name": med_name,
                        "dosage": dosage,
                        "timing": timing,
                        "total": total_count,
                        "remaining": total_count,
                        "taken_today": False
                    })
                    st.success(f"✅ {med_name} added successfully!")
                else:
                    st.error("❌ Please fill all fields!")

        # Show Medicine List
        st.markdown("### 📋 Your Medicines Today")
        if "medicines" not in st.session_state or len(st.session_state.medicines) == 0:
            st.info("No medicines added yet. Add your first medicine above!")
        else:
            for i, med in enumerate(st.session_state.medicines):
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        st.markdown(f"**💊 {med['name']}** — {med['dosage']}")
                        st.caption(f"⏰ {med['timing']}")
                    with col2:
                        st.metric("Remaining", f"{med['remaining']} tablets")
                    with col3:
                        if not med["taken_today"]:
                            if st.button(f"✅ Took it!", key=f"took_{i}", use_container_width=True):
                                st.session_state.medicines[i]["taken_today"] = True
                                st.session_state.medicines[i]["remaining"] -= 1
                                st.success(f"Great! {med['name']} marked as taken!")
                                st.rerun()
                        else:
                            st.success("✅ Taken Today!")

                    # Low stock warning
                    if med["remaining"] <= 5:
                        st.warning(f"⚠️ Low Stock! Only {med['remaining']} tablets left. Please refill!")
                    st.divider()

    # =====================
    # FAMILY DASHBOARD
    # =====================
    elif st.session_state.user_type == "family":
        st.markdown("## 👨‍👩‍👧 Family Dashboard")
        st.info("👀 Monitoring your loved one's medicines")

        if "medicines" not in st.session_state or len(st.session_state.medicines) == 0:
            st.warning("No medicines added yet by senior citizen!")
        else:
            st.markdown("### 📊 Medicine Status")
            for med in st.session_state.medicines:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown(f"**💊 {med['name']}** — {med['dosage']}")
                    st.caption(f"⏰ {med['timing']}")
                with col2:
                    if med["taken_today"]:
                        st.success("✅ Taken")
                    else:
                        st.error("❌ Not Taken")
                if med["remaining"] <= 5:
                    st.warning(f"⚠️ {med['name']} running low! Only {med['remaining']} left!")
                st.divider()