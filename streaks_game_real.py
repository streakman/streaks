import streamlit as st
import requests
import openai
import datetime
import random
import json
import time

# === Configuration ===
THESPORTSDB_API_KEY = "123/"  # <-- Replace with your actual key
OPENAI_API_KEY = "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"   # <-- Replace with your actual OpenAI key
THESPORTSDB_BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}"
openai.api_key = OPENAI_API_KEY

# === Helper Functions ===
def fetch_random_team_id():
    leagues = ["NBA", "NFL", "NHL", "MLB"]
    league = random.choice(leagues)
    url = f"{THESPORTSDB_BASE_URL}/search_all_teams.php?l={league}"
    res = requests.get(url)
    if res.status_code != 200:
        st.error("Error fetching teams from TheSportsDB")
        return None
    try:
        teams = res.json()["teams"]
        team = random.choice(teams)
        return team["idTeam"], team["strTeam"]
    except Exception as e:
        st.error(f"Failed to extract team data: {e}")
        return None

def fetch_team_players(team_id):
    url = f"{THESPORTSDB_BASE_URL}/lookup_all_players.php?id={team_id}"
    res = requests.get(url)
    if res.status_code != 200:
        st.error("Error fetching players from TheSportsDB")
        return None
    try:
        return res.json()["player"]
    except Exception as e:
        st.error(f"Failed to extract player data: {e}")
        return None

def generate_trivia_questions(summary_data):
    prompt = f"""
    You are a sports trivia AI. Based on the following data:
    {summary_data}
    Generate 10 multiple-choice sports trivia questions about teams, players, or historical stats across sports. Each question must have 4 answer choices and one correct answer clearly marked.
    Respond in JSON format:
    [{{"question": ..., "choices": [..], "correct_answer": ...}}, ...]
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1100
    )
    try:
        questions = json.loads(response["choices"][0]["message"]["content"])
        return questions
    except Exception as e:
        st.error(f"Error parsing GPT response: {e}")
        return []

def get_today_questions():
    today = datetime.date.today().isoformat()
    filename = f"questions_{today}.json"
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        # Generate new questions
        team_id, team_name = fetch_random_team_id()
        players = fetch_team_players(team_id)
        data_summary = json.dumps(players)
        questions = generate_trivia_questions(data_summary)
        with open(filename, "w") as f:
            json.dump(questions, f)
        return questions

def update_user_stats(username, correct_count):
    today = datetime.date.today().isoformat()
    stats_file = f"stats_{today}.json"
    try:
        with open(stats_file, "r") as f:
            stats = json.load(f)
    except:
        stats = {}
    if username not in stats:
        stats[username] = {"score": 0}
    stats[username]["score"] += correct_count
    with open(stats_file, "w") as f:
        json.dump(stats, f)

# === Streamlit UI ===
st.title("🏆 Daily Sports Streaks Game")

username = st.text_input("Enter your name to begin:")
if username:
    questions = get_today_questions()
    correct = 0

    for i, q in enumerate(questions):
        st.markdown(f"### Question {i + 1}: {q['question']}")

        # Countdown timer
        count = st.empty()
        for sec in range(10, 0, -1):
            count.markdown(f"⏱️ Time left: {sec}s")
            time.sleep(1)
        count.markdown("⏱️ Time's up!")

        choice = st.radio("Choose an answer:", q['choices'], key=f"q{i}")
        if st.button(f"Submit Answer {i + 1}", key=f"submit_{i}"):
            if choice == q['correct_answer']:
                st.success("✅ Correct!")
                correct += 1
            else:
                st.error(f"❌ Wrong. Correct answer was: {q['correct_answer']}")

    st.markdown(f"## ✅ You got {correct} out of {len(questions)} correct!")
    update_user_stats(username, correct)

    st.markdown("### 📊 Leaderboard (Today)")
    try:
        with open(f"stats_{datetime.date.today().isoformat()}.json", "r") as f:
            stats = json.load(f)
        sorted_stats = sorted(stats.items(), key=lambda x: -x[1]['score'])
        for rank, (user, data) in enumerate(sorted_stats, 1):
            st.write(f"{rank}. {user} - {data['score']} points")
    except:
        st.info("No stats yet for today.")
