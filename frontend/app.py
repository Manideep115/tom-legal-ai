import streamlit as st

st.set_page_config(page_title="Indian Legal AI Portal", page_icon="⚖️", layout="wide")

st.title("⚖️ Indian Legal Intelligence Portal")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.header("🔍 General Q&A")
    st.write("Ask questions about BNS, BNSS, and BSA. Perfect for quick legal research and definitions.")
    if st.button("Open Assistant"):
        st.switch_page("pages/1_QA_assistant.py")

with col2:
    st.header("🤖 Tom: Case Dashboard")
    st.write("Upload FIRs or legal notices. Tom will analyze the facts, build timelines, and visualize the case.")
    if st.button("Launch Tom"):
        st.switch_page("pages/2_tom_deep_dashboard.py")

st.info("Select a tool from the sidebar or click a button above to get started.")
