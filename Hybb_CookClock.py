import streamlit as st
import time
from datetime import datetime, date, time as dt_time
from streamlit_autorefresh import st_autorefresh
import threading

# ==========================
# CONFIGURATION
# ==========================
st.set_page_config(page_title="HYBB CookClock", layout="wide")
st.title("🍳 HYBB CookClock - Kitchen Timer")

# Auto-refresh every second for timers
st_autorefresh(interval=1000, key="refresh")

# ==========================
# DEFAULT SOUND (ALARM)
# ==========================
# Base64-encoded WAV alarm (works on mobile)
alarm_base64 = (
    "UklGRkQAAABXQVZFZm10IBAAAAABAAEAIlYAAESsAAACABAAZGF0YQAAAAAA////"
    "/////////////////////wAA/////wAA/////wAA/////wAA/////wAA/////wAA"
    "/////wAA/////wAA/////wAA"
)

# Embed alarm audio and JS functions
st.markdown(f"""
<audio id="alarmSound" preload="auto" loop>
  <source src="data:audio/wav;base64,{alarm_base64}" type="audio/wav">
</audio>

<script>
let alarmUnlocked = false;
const alarmSound = document.getElementById("alarmSound");

// Unlock sound on first tap/click (mobile)
document.addEventListener("click", () => {{
  if (!alarmUnlocked) {{
    alarmSound.play().then(() => {{
      alarmSound.pause();
      alarmSound.currentTime = 0;
      alarmUnlocked = true;
      console.log("Alarm unlocked ✅");
    }}).catch(() => {{}});
  }}
}}, {{once:true}});

// Global functions to play/stop alarm from Streamlit
window.playAlarm = function() {{
  alarmSound.currentTime = 0;
  alarmSound.play().catch((e)=>console.log("Play blocked:", e));
}};
window.stopAlarm = function() {{
  alarmSound.pause();
  alarmSound.currentTime = 0;
}};
</script>
""", unsafe_allow_html=True)

# ==========================
# TASK TIMER LOGIC
# ==========================
if "running_tasks" not in st.session_state:
    st.session_state.running_tasks = {}

# Predefined kitchen items
task_options = {
    "Kebab": 90,
    "Wings": 90,
    "Harabara Kebab": 180,
}

# --- Start new task ---
st.subheader("▶️ Start New Timer")
col1, col2, col3 = st.columns([2,1,1])
with col1:
    selected_task = st.selectbox("Select Item", list(task_options.keys()))
with col2:
    qty = st.number_input("Quantity", 1, 50, 1)
with col3:
    start_btn = st.button("Start Timer")

if start_btn:
    duration = task_options[selected_task]
    start_time = datetime.now()
    end_time = start_time.timestamp() + duration
    key = f"{selected_task}_{start_time.timestamp()}"
    st.session_state.running_tasks[key] = {
        "item": selected_task,
        "qty": qty,
        "end_time": end_time,
        "started": start_time.strftime("%H:%M:%S"),
        "duration": duration
    }
    st.success(f"⏱ {selected_task} started for {duration} seconds")

# ==========================
# DISPLAY RUNNING TIMERS
# ==========================
st.subheader("⏳ Running Timers")
if st.session_state.running_tasks:
    to_remove = []
    for key, data in st.session_state.running_tasks.items():
        remaining = int(data["end_time"] - time.time())
        if remaining > 0:
            st.info(f"🧑‍🍳 {data['item']} (x{data['qty']}) → {remaining}s left")
        else:
            st.warning(f"✅ {data['item']} READY!")
            # Play alarm on frontend
            st.markdown('<script>if(window.playAlarm) window.playAlarm();</script>', unsafe_allow_html=True)
            to_remove.append(key)

    # Remove finished tasks
    for r in to_remove:
        del st.session_state.running_tasks[r]
else:
    st.write("No active timers.")

# ==========================
# MANUAL ALARM CONTROL
# ==========================
st.markdown("---")
st.subheader("🔊 Manual Alarm Controls")
colA, colB = st.columns(2)
with colA:
    st.markdown(
        '<button onclick="window.playAlarm()" '
        'style="font-size:20px;padding:10px 20px;background-color:green;color:white;'
        'border:none;border-radius:10px;">Play Alarm</button>',
        unsafe_allow_html=True,
    )
with colB:
    st.markdown(
        '<button onclick="window.stopAlarm()" '
        'style="font-size:20px;padding:10px 20px;background-color:red;color:white;'
        'border:none;border-radius:10px;">Stop Alarm</button>',
        unsafe_allow_html=True,
    )

st.markdown("<p style='color:gray;'>Tip: Tap Play Alarm once to unlock sound on mobile.</p>", unsafe_allow_html=True)
