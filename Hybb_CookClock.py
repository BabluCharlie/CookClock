import streamlit as st
import time
from datetime import datetime, date, time as dt_time
from streamlit_autorefresh import st_autorefresh
import threading
import streamlit.components.v1 as components
import base64
import os

# ==========================
# CONFIGURATION
# ==========================
st.set_page_config(page_title="HYBB CookClock", layout="wide")
AUTO_CLEAR_SECONDS = 15  # Auto-remove done tasks

# Predefined tasks (seconds)
predefined_tasks = {
    "Kebab Frying": 90,
    "Rice Cooking": 25 * 60,
    "Test 1": 10,
    "Water Motor": 30 * 60
}

# Task colors
TASK_COLORS = {
    "Kebab Frying": "#e67e22",
    "Rice Cooking": "#3498db",
    "Test 1": "#f1c40f",
    "Water Motor": "#1abc9c",
    "Custom": "#9b59b6",
    "Scheduled": "#f39c12",
    "Upcoming": "#d35400"
}

# Store active tasks
if "active_tasks" not in st.session_state:
    st.session_state.active_tasks = {}

# Auto-refresh for timer updates
st_autorefresh(interval=1000, key="timer_refresh")

# ==========================
# Beep setup: local file or fallback Base64
# ==========================
BEEP_FILE = "beep-01a.wav"

if os.path.exists(BEEP_FILE):
    with open(BEEP_FILE, "rb") as f:
        beep_base64 = base64.b64encode(f.read()).decode()
else:
    st.warning(f"Beep file '{BEEP_FILE}' not found. Using default beep.")
    beep_base64 = (
        "UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YRAAAAAA////"
        "/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA/////wAA"
    )

# ==========================
# JS beep function (3 repeated beeps)
# ==========================
def trigger_alarm(task_name):
    st.toast(f"Task '{task_name}' completed!")

    # Desktop autoplay works, mobile shows button if blocked
    components.html(f"""
    <div style='text-align:center; margin-top:10px;'>
        <button onclick="document.getElementById('alarm').play();" 
            style="background-color:#ff4444;color:white;font-size:20px;
                   padding:12px 24px;border:none;border-radius:10px;cursor:pointer;
                   animation: flash 1s infinite;">
            🔔 Play Sound for {task_name}
        </button>
    </div>
    <audio id="alarm" autoplay>
        <source src="data:audio/wav;base64,{beep_base64}" type="audio/wav">
    </audio>
    <style>
    @keyframes flash {{
      0% {{ background-color:#ff4444; }}
      50% {{ background-color:#ffbb33; }}
      100% {{ background-color:#ff4444; }}
    }}
    </style>
    """, height=100)

# ==========================
# Helper functions
# ==========================
def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"

def start_task(task_name, duration, task_type="Custom", scheduled_datetime=None):
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
        "alarm_played": False,          # Desktop autoplay
        "alarm_played_manual": False    # Mobile manual trigger
    }

def display_task(task, key):
    sched_str = task["scheduled_datetime"].strftime("%Y-%m-%d %H:%M") if task.get("scheduled_datetime") else ""
    status = task["status"]
    color = "#28a745" if status == "Done" else task["color"]
    percent = int((task["remaining"] / task["duration"]) * 100) if status == "Running" and task["duration"] > 0 else 0
    remaining_str = format_time(task["remaining"]) if status != "Scheduled" else "--:--"

    task["placeholder"].markdown(f"""
    <div style='border:2px solid {color}; padding:20px; margin-bottom:15px; border-radius:15px;
                background-color:#fef9f4; box-shadow: 4px 4px 12px #ccc;' >
        <h1 style='margin:0; color:{color}; font-family:"Impact","Arial Black",sans-serif;
                   font-weight:bold; font-size:48px; text-shadow: 2px 2px #ddd;'>{task['name']}</h1>
        <p style='margin:5px 0; font-size:20px; font-weight:bold;'>Scheduled: {sched_str}</p>
        <p style='margin:10px 0; font-size:24px; font-weight:bold;'>Remaining: {remaining_str}</p>
        <div style='background-color:#eee; border-radius:12px; overflow:hidden; height:25px;' >
            <div style='width:{percent}%; background-color:{color}; height:25px; transition: width 1s;'></div>
        </div>
        <p style='margin:10px 0; font-size:20px; font-weight:bold;'>Status: {status}</p>
    </div>
    """, unsafe_allow_html=True)

    if status == "Running":
        pause_key = task["pause_key"]
        task["paused"] = st.checkbox("Pause/Resume", key=pause_key)
    else:
        task["paused"] = False

def update_tasks():
    now = datetime.now()
    for key, task in list(st.session_state.active_tasks.items()):
        # Activate scheduled tasks
        if task["status"] == "Scheduled" and task.get("scheduled_datetime") and task["scheduled_datetime"] <= now:
            task["status"] = "Running"

        # Countdown for running tasks
        if task["status"] == "Running" and not task.get("paused", False):
            task["remaining"] -= 1
            if task["remaining"] <= 0:
                task["status"] = "Done"
                task["remaining"] = 0
                if not task.get("alarm_played", False):
                    trigger_alarm(task["name"])
                    task["alarm_played"] = True
                threading.Timer(AUTO_CLEAR_SECONDS, lambda k=key: st.session_state.active_tasks.pop(k, None)).start()

# ==========================
# UI LAYOUT
# ==========================
st.markdown("<h1 style='text-align:center; color:#d35400;'>🍖🍚🥘 HYBB CookClock 🥘🍚🍖</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Mobile-friendly Manual Beep Trigger ---
st.subheader("🔔 Play Beeps for Completed Tasks (Tap on Mobile)")
if st.button("Play Beeps for Finished Tasks"):
    for key, task in st.session_state.active_tasks.items():
        if task["status"] == "Done" and not task.get("alarm_played_manual", False):
            trigger_alarm(task["name"])
            task["alarm_played_manual"] = True

# Predefined Tasks
st.subheader("🔥 Predefined Tasks")
cols = st.columns(len(predefined_tasks))
for i, (task_name, duration) in enumerate(predefined_tasks.items()):
    with cols[i]:
        if st.button(f"Start {task_name}", key=f"start_{task_name}"):
            start_task(task_name, duration, task_type=task_name)

st.markdown("---")

# Custom Task - immediate start
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

# Scheduled Custom Task
st.subheader("⏰ Schedule Task for Future")
with st.form("scheduled_task_form"):
    sched_name = st.text_input("Task Name (Scheduled)")
    sched_date = st.date_input("Select Date", value=date.today())
    sched_time = st.time_input("Select Time", value=dt_time(12, 0))
    sched_min = st.number_input("Minutes", min_value=0, value=0, key="sched_min")
    sched_sec = st.number_input("Seconds", min_value=0, value=30, key="sched_sec")
    submitted_sched = st.form_submit_button("Schedule Task")
    if submitted_sched:
        duration = int(sched_min)*60 + int(sched_sec)
        scheduled_datetime = datetime.combine(sched_date, sched_time)
        start_task(sched_name, duration, task_type="Scheduled", scheduled_datetime=scheduled_datetime)

st.markdown("---")

# Upcoming Tasks Section (Scheduled only)
st.subheader("📅 Upcoming Tasks")
for key, task in st.session_state.active_tasks.items():
    if task["status"] == "Scheduled":
        task["color"] = TASK_COLORS["Upcoming"]
        task["paused"] = False
        display_task(task, key)

# ==========================
# Update all tasks and display Running/Done tasks
# ==========================
update_tasks()

st.subheader("⏱️ Active Tasks")
for key, task in st.session_state.active_tasks.items():
    if task["status"] != "Scheduled":
        display_task(task, key)
