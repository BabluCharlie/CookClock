import streamlit as st
import time
from datetime import datetime, timedelta
import threading
import streamlit.components.v1 as components

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(page_title="HYBB CookClock", page_icon="🍳", layout="centered")

# ==========================
# TITLE AND STYLE
# ==========================
st.markdown(
    """
    <style>
    .main {background-color: #fff8f0;}
    .stButton>button {
        border-radius: 12px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: 600;
        background-color: #faae42;
        color: black;
        border: none;
    }
    .stButton>button:hover {
        background-color: #f9c76f;
        color: black;
    }
    .flashing {
        animation: flash 1s infinite;
    }
    @keyframes flash {
        0% {background-color: #f87171;}
        50% {background-color: #22c55e;}
        100% {background-color: #f87171;}
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🍳 HYBB CookClock Timer")

# ==========================
# SOUND UNLOCK SECTION
# ==========================

# JS block for unlocking sound (mobile browsers require user interaction)
sound_unlock_html = """
<script>
let soundEnabled = false;
function unlockSound() {
  const context = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = context.createOscillator();
  oscillator.connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + 0.1);
  soundEnabled = true;
  const msg = document.getElementById("soundStatus");
  msg.innerText = "✅ Sound Enabled! You’ll now hear alerts.";
  msg.style.color = "green";
}
</script>
<div style="text-align:center;">
  <button onclick="unlockSound()" class="flashing" 
    style="font-size:18px;padding:12px 24px;border:none;border-radius:12px;color:white;">
    🔊 Enable Sound for Alarms
  </button>
  <p id="soundStatus" style="font-weight:600;color:red;">(Tap the button above to enable sound)</p>
</div>
"""

components.html(sound_unlock_html, height=160)

# ==========================
# BEEP FUNCTION (JS)
# ==========================
beep_js = """
<script>
function playBeep() {
    try {
        const context = new (window.AudioContext || window.webkitAudioContext)();
        const o = context.createOscillator();
        const g = context.createGain();
        o.connect(g);
        g.connect(context.destination);
        o.type = "sine";
        o.frequency.setValueAtTime(880, context.currentTime);
        g.gain.setValueAtTime(0.2, context.currentTime);
        o.start();
        o.stop(context.currentTime + 0.5);
    } catch (e) {
        console.log("Sound blocked:", e);
    }
}
</script>
"""

components.html(beep_js)

def play_beep():
    components.html("<script>playBeep();</script>", height=0)

# ==========================
# TIMER STORAGE
# ==========================
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# ==========================
# ADD NEW TIMER
# ==========================
with st.expander("➕ Add New Timer", expanded=True):
    task_name = st.text_input("Task Name")
    duration = st.number_input("Duration (seconds)", min_value=10, step=10)
    add_btn = st.button("Start Timer")

if add_btn and task_name:
    end_time = datetime.now() + timedelta(seconds=duration)
    st.session_state.tasks.append({
        "name": task_name,
        "end_time": end_time,
        "done": False
    })
    st.success(f"⏳ Timer started for {task_name} ({duration}s)")

# ==========================
# DISPLAY ACTIVE TIMERS
# ==========================
st.subheader("⏱ Active Timers")

active_found = False
for i, task in enumerate(st.session_state.tasks):
    if not task["done"]:
        active_found = True
        remaining = (task["end_time"] - datetime.now()).total_seconds()
        if remaining <= 0:
            st.error(f"✅ {task['name']} finished!")
            play_beep()
            st.session_state.tasks[i]["done"] = True
        else:
            mins, secs = divmod(int(remaining), 60)
            st.info(f"{task['name']}: {mins:02d}:{secs:02d} remaining")

if not active_found:
    st.write("No active timers.")

# ==========================
# REFRESH
# ==========================
st_autorefresh = st.experimental_rerun
time.sleep(1)
