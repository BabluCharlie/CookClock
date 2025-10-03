import streamlit as st
from datetime import datetime, date, time as dt_time
from pathlib import Path
from streamlit_autorefresh import st_autorefresh

# ==========================
# CONFIGURATION
# ==========================
st.set_page_config(page_title="HYBB CookClock", layout="wide")
AUTO_CLEAR_SECONDS = 15  # auto-remove done tasks

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

# Initialize session state
if "active_tasks" not in st.session_state:
    st.session_state.active_tasks = {}


# ==========================
# HELPER FUNCTIONS
# ==========================
def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"


def play_web_alarm():
    """Play audio alert in Streamlit (mobile & desktop)"""
    audio_file = Path("alarm.wav")
    if audio_file.exists():
        st.audio(str(audio_file), format="audio/wav")
    st.toast("🔔 Task completed!")


def trigger_alarm(task_name):
    play_web_alarm()
    st.toast(f"Task '{task_name}' completed!")


def start_task(task_name, duration, task_type="Custom", scheduled_datetime=None):
    key = f"{task_name}_{len(st.session_state.active_tasks)}"
    pause_key = f"pause_{key}"
    placeholder = st.empty()

    if pause_key not in st.session_state:
        st.session_state[pause_key] = False

    status = "Scheduled" if scheduled_datetime and scheduled_datetime > datetime.now() else "Running"

    st.session_state.active_tasks[key] = {
        "name": task_name,
        "duration": duration,
        "remaining": duration,
        "status": status,
        "color": TASK_COLORS.get(task_type, TASK_COLORS["Custom"]),
        "pause_key": pause_key,
        "scheduled_datetime": scheduled_datetime,
        "alarm_played": False,
        "placeholder": placeholder
    }


def update_tasks():
    now = datetime.now()
    for key, task in list(st.session_state.active_tasks.items()):
        # Activate scheduled tasks
        if task["status"] == "Scheduled" and task.get("scheduled_datetime") and task["scheduled_datetime"] <= now:
            task["status"] = "Running"

        # Countdown if running and not paused
        if task["status"] == "Running" and not st.session_state.get(task["pause_key"], False):
            task["remaining"] -= 1
            if task["remaining"] <= 0:
                task["remaining"] = 0
                task["status"] = "Done"
                if not task["alarm_played"]:
                    trigger_alarm(task["name"])
                    task["alarm_played"] = True

        # Auto-remove done tasks after delay
        if task["status"] == "Done":
            task["remaining"] = 0


def display_task(task):
    pause_key = task["pause_key"]
    if pause_key not in st.session_state:
        st.session_state[pause_key] = False

    task["paused"] = st.session_state[pause_key]
    status = task["status"]
    color = "#28a745" if status == "Done" else task["color"]
    percent = int((task["remaining"] / task["duration"]) * 100) if task["duration"] > 0 else 0
    remaining_str = format_time(task["remaining"]) if status != "Scheduled" else "--:--"
    sched_str = task["scheduled_datetime"].strftime("%Y-%m-%d %H:%M") if task.get("scheduled_datetime") else ""

    with task["placeholder"]:
        st.markdown(f"""
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
        st.checkbox("Pause/Resume", key=pause_key)


# ==========================
# UI LAYOUT
# ==========================
st.markdown("<h1 style='text-align:center; color:#d35400;'>🍖🍚🥘 HYBB CookClock 🥘🍚🍖</h1>", unsafe_allow_html=True)
st.markdown("---")

# Predefined Tasks
st.subheader("🔥 Predefined Tasks")
cols = st.columns(len(predefined_tasks))
for i, (task_name, duration) in enumerate(predefined_tasks.items()):
    with cols[i]:
        if st.button(f"Start {task_name}", key=f"start_{task_name}"):
            start_task(task_name, duration, task_type=task_name)

# Custom Task Form
st.subheader("✨ Add Custom Task (Immediate)")
with st.form("custom_task_form"):
    custom_name = st.text_input("Task Name")
    custom_min = st.number_input("Minutes", min_value=0, value=0)
    custom_sec = st.number_input("Seconds", min_value=0, value=30)
    submitted = st.form_submit_button("Start Task")
    if submitted:
        duration = int(custom_min) * 60 + int(custom_sec)
        start_task(custom_name, duration, task_type="Custom")

# Scheduled Task Form
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

# Update and display all tasks
update_tasks()
for task in st.session_state.active_tasks.values():
    display_task(task)

# Auto-refresh every second
st_autorefresh(interval=1000, limit=None, key="refresh")
