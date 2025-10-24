import streamlit as st
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================
# CONFIG
# ==========================
st.set_page_config(page_title="HYBB CookClock", layout="wide")
st.title("🍳 HYBB CookClock - Kitchen Timer")

st_autorefresh(interval=1000, key="refresh")  # refresh every 1s

# ==========================
# ALARM SETUP
# ==========================
alarm_base64 = (
    "UklGRkQAAABXQVZFZm10IBAAAAABAAEAIlYAAESsAAACABAAZGF0YQAAAAAA////"
    "/////////////////////wAA/////wAA/////wAA/////wAA/////wAA/////wAA"
    "/////wAA/////wAA/////wAA"
)

st.markdown(f"""
<audio id="alarmAudio" preload="auto" loop>
  <source src="data:audio/wav;base64,{alarm_base64}" type="audio/wav">
</audio>

<script>
window.playAlarm = function() {{
    const audio = document.getElementById("alarmAudio");
    audio.currentTime = 0;
    audio.play().catch(()=>console.log("Play blocked"));
}};
window.stopAlarm = function() {{
    const audio = document.getElementById("alarmAudio");
    audio.pause();
    audio.currentTime = 0;
}};
</script>
""", unsafe_allow_html=True)

# ==========================
# TASKS
# ==========================
if "tasks" not in st.session_state:
    st.session_state.tasks = {}

task_options = {
    "Kebab": 90,
    "Wings": 90,
    "Harabara Kebab": 180
}

st.subheader("Start Timer")
col1, col2, col3 = st.columns([2, 1, 1])
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
st.subheader("Running Timers")
finished_tasks = []
for key, t in st.session_state.tasks.items():
    remaining = int(t["end_time"] - time.time())
    if remaining > 0:
        st.info(f"🧑‍🍳 {t['item']} (x{t['qty']}) → {remaining}s left")
    else:
        st.error(f"✅ {t['item']} READY!")
        # Show manual play alarm button
        st.markdown(f"""
        <button onclick="window.playAlarm()"
            style="font-size:24px;padding:10px 20px;background-color:red;color:white;border:none;border-radius:10px;">
            🔊 Play Alarm
        </button>
        """, unsafe_allow_html=True)
        finished_tasks.append(key)

# Remove finished tasks
for key in finished_tasks:
    del st.session_state.tasks[key]

# ==========================
# MANUAL ALARM CONTROLS
# ==========================
st.markdown("---")
st.subheader("Manual Alarm Controls")
colA, colB = st.columns(2)
with colA:
    st.markdown(
        '<button onclick="window.playAlarm()" style="font-size:20px;padding:10px 20px;background-color:green;color:white;border:none;border-radius:10px;">Play Alarm</button>',
        unsafe_allow_html=True
    )
with colB:
    st.markdown(
        '<button onclick="window.stopAlarm()" style="font-size:20px;padding:10px 20px;background-color:red;color:white;border:none;border-radius:10px;">Stop Alarm</button>',
        unsafe_allow_html=True
    )

st.markdown("<p style='color:gray;'>⚠️ Tip: On mobile, you must tap 'Play Alarm' once to unlock sound.</p>", unsafe_allow_html=True)
