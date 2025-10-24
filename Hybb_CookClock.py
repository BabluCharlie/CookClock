import streamlit as st
import time
from datetime import datetime, date, time as dt_time
from streamlit_autorefresh import st_autorefresh
import threading

# ==========================
# CONFIGURATION
# ==========================
st.set_page_config(page_title="HYBB CookClock", layout="wide")
AUTO_CLEAR_SECONDS = 15  # Auto-remove done tasks after X seconds

# Predefined tasks
predefined_tasks = {
    "Kebab Frying": 90,
    "Rice Cooking": 25 * 60,
    "Test 1": 10,
    "Water Motor": 30 * 60
}

TASK_COLORS = {
    "Kebab Frying": "#e67e22",
    "Rice Cooking": "#3498db",
    "Test 1": "#f1c40f",
    "Water Motor": "#1abc9c",
    "Custom": "#9b59b6",
    "Scheduled": "#f39c12",
    "Upcoming": "#d35400"
}

if "active_tasks" not in st.session_state:
    st.session_state.active_tasks = {}

st_autorefresh(interval=1000, key="timer_refresh")

# ==========================
# SOUND FIX (WORKS ON MOBILE)
# ==========================
beep_base64 = (
    "UklGRjQAAABXQVZFZm10IBAAAAABAAEAIlYAAESsAAACABAAZGF0YQAAAAA////"
    "/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA"
)

# Persistent audio element + JS helpers (escaped braces)
st.markdown(f"""
<audio id="beepAudio" preload="auto">
  <source src="data:audio/wav;base64,{beep_base64}" type="audio/wav">
</audio>

<script>
let beepUnlocked = false;
const beepAudio = document.getElementById("beepAudio");

// Unlock audio on first user click (mobile browsers block autoplay)
document.addEventListener("click", () => {{
  if (!beepUnlocked) {{
    beepAudio.play().then(() => {{
      beepAudio.pause();
      beepAudio.currentTime = 0;
      beepUnlocked = true;
      console.log("Beep unlocked ✅");
    }}).catch(() => {{ }});
  }}
}}, {{once:true}});

// Global JS function Streamlit can call
window.playBeep = function() {{
  beepAudio.currentTime = 0;
  beepAudio.play().catch((e) => {{
    console.log("Play blocked:", e);
  }});
}};
</script>
""", unsafe_allow_html=True)

# Manual beep button (for mobile unlock or testing)
st.markdown("""
<div style="text-align:center; margin:10px;">
  <button onclick="window.playBeep()" 
    style="background:#ff6b00;color:white;font-size:22px;
           border:none;border-radius:10px;padding:10px 25px;
           animation:flash 1s infinite;cursor:pointer;">
    🔊 Play Beep
  </button>
</div>

<style>
@keyframes flash {
  0%,100% { background-color:#ff6b00; }
  50% { background-color:#ffbb33; }
}
</style>
""", unsafe_allow_html=True)

# ==========================
# HELPER FUNCTIONS
# ==========================
def trigger_alarm(task_name):
    """Play beep and show toast when a task completes"""
    st.toast(f"✅ Task '{task_name}' completed!")
    st.markdown("<script>window.playBeep();</script>", unsafe_allow_html=True)

def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"

def start_task(task_name, duration, task_type="Custom", scheduled_datetime=None):
    """Start or schedule a task"""
    key = f"{task_name}_{len(st.session_state.active_tasks)}"
    placeholder = st.empty()
    color = TASK_COLORS.get(task_type, TASK_COLORS["Custom"])
    status = "Scheduled" if scheduled_datetime and scheduled_datetime > datetime.now() else "Running"
    pause_key = f"pause_{key}"
    if pause_key not in st.session_state:
        st.session_state[pause_key] = False
    st.session_state.active_tasks[key] = {
        "name": task_name,
        "duration": duration,
        "remaining": duration,
        "status": status,
        "placeholder": placeholder,
        "color": color,
        "pause_key": pause_key,
        "scheduled_datetime": scheduled_datetime,
        "alarm_played": False
    }

def display_task(task, key):
    """Render a single task card"""
    sched_str = task["scheduled_datetime"].strftime("%Y-%m-%d %H:%M") if task.get("scheduled_datetime") else ""
    status = task["status"]
    color = "#28a745" if status == "Done" else task["color"]
    percent = int((task["remaining"] / task["duration"]) * 100) if status == "Running" and task["duration"] > 0 else 0
    remaining_str = format_time(task["remaining"]) if status != "Scheduled" else "--:--"

    task["placeholder"].markdown(f"""
    <div style='border:2px solid {color}; padding:20px; margin-bottom:15px; border-radius:15px;
                background-color:#fff7f0; box-shadow: 4px 4px 12px #ccc;' >
        <h1 style='margin:0; color:{color}; font-family:"Impact","Arial Black",sans-serif;
                   font-weight:bold; font-size:48px; text-shadow: 2px 2px #ddd;'>{task['name']}</h1>
        <p style='font-size:20px;'>Scheduled: {sched_str}</p>
        <p style='font-size:24px;'>Remaining: {remaining_str}</p>
        <div style='background-color:#eee; border-radius:12px; overflow:hidden; height:25px;' >
            <div style='width:{percent}%; background-color:{color}; height:25px; transition: width 1s;'></div>
        </div>
        <p style='font-size:20px;'>Status: {status}</p>
    </div>
    """, unsafe_allow_html=True)

    if status == "Running":
        task["paused"] = st.checkbox("Pause/Resume", key=task["pause_key"])
    else:
        task["paused"] = False

def update_tasks():
    """Update timers and trigger alarms"""
    now = datetime.now()
    for key, task in list(st.session_state.active_tasks.items()):
        if task["status"] == "Scheduled" and task["scheduled_datetime"] <= now:
            task["status"] = "Running"
        if task["status"] == "Running" and not task.get("paused", False):
            task["remaining"] -= 1
            if task["remaining"] <= 0:
                task["status"] = "Done"
                task["remaining"] = 0
                if not task["alarm_played"]:
                    trigger_alarm(task["name"])
                    task["alarm_played"] = True
                # Auto-clear after a short delay
                threading.Timer(AUTO_CLEAR_SECONDS, lambda k=key: st.session_state.active_tasks.pop(k, None)).start()

# ==========================
# UI SECTION
# ==========================
st.markdown("<h1 style='text-align:center; color:#d35400;'>🍖🍚🥘 HYBB CookClock 🥘🍚🍖</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Predefined Tasks ---
st.subheader("🔥 Predefined Tasks")
cols = st.columns(len(predefined_tasks))
for i, (task_name, duration) in enumerate(predefined_tasks.items()):
    with cols[i]:
        if st.button(f"Start {task_name}", key=f"start_{task_name}"):
            start_task(task_name, duration, task_type=task_name)

st.markdown("---")

# --- Custom Task (Immediate) ---
st.subheader("✨ Add Custom Task (Immediate)")
with st.form("custom_task_form"):
    custom_name = st.text_input("Task Name")
    custom_min = st.number_input("Minutes", min_value=0, value=0)
    custom_sec = st.number_input("Seconds", min_value=0, value=30)
    submitted = st.form_submit_button("Start Task")
    if submitted:
        duration = int(custom_min) * 60 + int(custom_sec)
        start_task(custom_name, duration, task_type="Custom")

st.markdown("---")

# --- Scheduled Task ---
st.subheader("⏰ Schedule Task for Future")
with st.form("scheduled_task_form"):
    sched_name = st.text_input("Task Name (Scheduled)")
    sched_date = st.date_input("Select Date", value=date.today())
    sched_time = st.time_input("Select Time", value=dt_time(12, 0))
    sched_min = st.number_input("Minutes", min_value=0, value=0, key="sched_min")
    sched_sec = st.number_input("Seconds", min_value=0, value=30, key="sched_sec")
    submitted_sched = st.form_submit_button("Schedule Task")
    if submitted_sched:
        duration = int(sched_min) * 60 + int(sched_sec)
        scheduled_datetime = datetime.combine(sched_date, sched_time)
        start_task(sched_name, duration, task_type="Scheduled", scheduled_datetime=scheduled_datetime)

st.markdown("---")

# --- Upcoming Tasks ---
st.subheader("📅 Upcoming Tasks")
for key, task in st.session_state.active_tasks.items():
    if task["status"] == "Scheduled":
        task["color"] = TASK_COLORS["Upcoming"]
        display_task(task, key)

# Update all timers
update_tasks()

# --- Active Tasks ---
st.subheader("⏱️ Active Tasks")
for key, task in st.session_state.active_tasks.items():
    if task["status"] != "Scheduled":
        display_task(task, key)
