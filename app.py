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
    if st.session_state.user_type == "senior":
        st.success("Welcome Senior Citizen! 👴")
        st.info("Medicine tracking dashboard coming soon!")
    else:
        st.success("Welcome Family Member! 👨‍👩‍👧")
        st.info("Family monitoring dashboard coming soon!")