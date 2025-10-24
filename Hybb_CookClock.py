import streamlit as st
import time
from datetime import datetime

# ==========================
# CONFIG
# ==========================
st.set_page_config(page_title="HYBB CookClock", layout="wide")
st.title("🍳 HYBB CookClock - Kitchen Timer")

# ==========================
# ALARM SOUND (built-in)
# ==========================
# Base64-encoded WAV beep (short)
import base64
import io

# Simple beep sound bytes
beep_bytes = base64.b64decode(
    "UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAAAB3AQACABAAZGF0YQAAAAA////"
    "/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA"
)

# ==========================
# TASK SETUP
# ==========================
if "tasks" not in st.session_state:
    st.session_state.tasks = {}

task_options = {
    "Kebab": 90,
    "Wings": 90,
    "Harabara Kebab": 180
}

# --- Start new task ---
st.subheader("▶️ Start New Timer")
col1, col2, col3 = st.columns([2,1,1])
with col1:
    selected_task = st.selectbox("Select Item", list(task_options.keys()))
with col2:
    qty = st.number_input("Quantity", 1, 50, 1)
with col3:
    if st.button("Start Timer"):
        key = f"{selected_task}_{time.time()}"
        st.session_state.tasks[key] = {
            "item": selected_task,
            "qty": qty,
            "duration": task_options[selected_task],
            "end_time": time.time() + task_options[selected_task]
        }

# ==========================
# RUNNING TIMERS
# ==========================
st.subheader("⏳ Running Timers")
finished_tasks = []
for key, t in st.session_state.tasks.items():
    remaining = int(t["end_time"] - time.time())
    if remaining > 0:
        st.info(f"🧑‍🍳 {t['item']} (x{t['qty']}) → {remaining}s left")
    else:
        st.error(f"✅ {t['item']} READY!")
        # Streamlit button to play sound
        if st.button(f"🔊 Play Alarm for {t['item']}"):
            st.audio(io.BytesIO(beep_bytes))
        finished_tasks.append(key)

# Remove finished tasks
for key in finished_tasks:
    del st.session_state.tasks[key]

# ==========================
# MANUAL ALARM CONTROL
# ==========================
st.markdown("---")
st.subheader("Manual Alarm")
colA, colB = st.columns(2)
with colA:
    if st.button("Play Alarm"):
        st.audio(io.BytesIO(beep_bytes))
with colB:
    st.write("Stop alarm by refreshing page.")
