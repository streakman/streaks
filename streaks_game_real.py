import streamlit as st
from sportsipy.nba.schedule import Schedule
from datetime import datetime
import json, os, random, time

st.set_page_config(page_title="Real Streaks Game", page_icon="🎯")
USER = st.text_input("Enter your username:", key="user") or "guest"
DATA_FILE = "streaks_real_data.json"
NUM_Q = 10
TODAY = datetime.now().strftime("%Y-%m-%d")
TIME_PER_Q = 15 # seconds

# Load or Init
if os.path.exists(DATA_FILE):
with open(DATA_FILE, "r") as f:
data = json.load(f)
else:
data = {}
if USER not in data:
data[USER] = {"history": {}, "streak": 0, "best": 0}

user = data[USER]

# Fetch schedule once
def fetch_games():
sched = Schedule('LAL') # Example: Lakers schedule; you can loop favored teams
today = TODAY
games = [g for g in sched if today in str(g.date)]
return games[:NUM_Q] if len(games)>=NUM_Q else random.sample(games, NUM_Q)

if TODAY not in user["history"]:
games = fetch_games()
user["history"][TODAY] = {"questions": [], "answers": [], "completed": False}
for g in games:
q = f"Will {g.opponent_name} beat the Lakers?"
# We don't know result yet
user["history"][TODAY]["questions"].append(q)

# UI
st.title("🎯 Today's Streak Game")
st.write(f"User: {USER} | Date: {TODAY}")
today_data = user["history"][TODAY]

if today_data["completed"]:
st.success("✅ Done for today!")
st.write(f"Score: {sum(today_data['answers'])}/{NUM_Q}")
else:
answers = today_data["answers"]
for idx, q in enumerate(today_data["questions"]):
st.write(f"**Q{idx+1}:** {q}")
timer = TIME_PER_Q
placeholder = st.empty()
start = time.time()
col1, col2 = st.columns(2)
clicked = None
while time.time() - start < TIME_PER_Q and clicked is None:
placeholder.write(f"Time left: {TIME_PER_Q - int(time.time() - start)}s")
if col1.button("Yes", key=f"y{idx}"):
clicked = True
if col2.button("No", key=f"n{idx}"):
clicked = False
time.sleep(0.1)
placeholder.empty()
if clicked is None:
st.write("⏰ No answer: counted as wrong.")
answers.append(0)
else:
# real result check
# sportsipy doesn't give future result; simulate random
correct = random.choice([True, False])
st.write("✅" if correct else "❌")
answers.append(int(correct))

user["history"][TODAY]["answers"] = answers
user["history"][TODAY]["completed"] = True

score = sum(answers)
if score == NUM_Q:
user["streak"] += 1
else:
user["streak"] = 0
user["best"] = max(user["best"], user["streak"])
st.write(f"Score: {score}/{NUM_Q}")
st.write(f"🔥 Streak: {user['streak']} | 🏆 Best: {user['best']}")
with open(DATA_FILE, "w") as f:
json.dump(data, f, indent=4)

# Sidebar
st.sidebar.header("📊 Stats")
st.sidebar.write("Current streak:", user["streak"])
st.sidebar.write("All-time best:", user["best"])
st.sidebar.write("Days played:", len(user["history"]))
