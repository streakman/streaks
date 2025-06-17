import streamlit as st
import requests
import json
import datetime
import os
import time
from openai import OpenAI

# ====== CONFIG =======
THESPORTSDB_API_KEY = "https://www.thesportsdb.com/api/v1/json/123/"
OPENAI_API_KEY = "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"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Local cache filename for daily questions
QUESTIONS_CACHE_FILE = "questions_cache.json"

# Fetch NBA player data from TheSportsDB API (example: Lakers roster)
def fetch_nba_top_scorers():
    url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchplayers.php?t=Los Angeles Lakers"
    res = requests.get(url)
    if res.status_code != 200:
        st.error(f"Error fetching data from TheSportsDB: {res.status_code}")
        return None
    try:
        data = res.json()
    except Exception as e:
        st.error(f"JSON decode error: {e}")
        return None
    return data

# Generate trivia questions using OpenAI GPT
def generate_trivia_questions(data_summary):
    messages = [
        {"role": "system", "content": "You are a creative sports trivia question generator."},
        {"role": "user", "content": f"Using this NBA player data summary: {data_summary}, generate 10 unique sports trivia questions across multiple sports with 4 multiple-choice options each. Format each question like this:\n\n1. Question text?\nA) option 1\nB) option 2\nC) option 3\nD) option 4\n\nOnly output the questions and options, no explanations."}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1100,
    )
    questions_text = response.choices[0].message.content
    return questions_text

# Save questions to cache with date key
def save_questions_cache(date_str, questions_text):
    cache = {}
    if os.path.exists(QUESTIONS_CACHE_FILE):
        with open(QUESTIONS_CACHE_FILE, "r") as f:
            cache = json.load(f)
    cache[date_str] = questions_text
    with open(QUESTIONS_CACHE_FILE, "w") as f:
        json.dump(cache, f)

# Load questions from cache if exists for today
def load_questions_cache(date_str):
    if not os.path.exists(QUESTIONS_CACHE_FILE):
        return None
    with open(QUESTIONS_CACHE_FILE, "r") as f:
        cache = json.load(f)
    return cache.get(date_str, None)

# Parse questions text into structured list
def parse_questions(questions_text):
    # Simple parser splitting by lines, this can be improved
    questions = []
    lines = questions_text.strip().split("\n")
    q = {}
    for line in lines:
        if line.strip() == "":
            continue
        if line[0].isdigit() and line[1] == ".":
            if q:
                questions.append(q)
            q = {"question": line[3:].strip(), "options": []}
        elif line[0] in ["A", "B", "C", "D"] and line[1] == ")":
            q["options"].append(line[3:].strip())
    if q:
        questions.append(q)
    return questions

# Streamlit countdown timer for each question
def countdown_timer(seconds):
    placeholder = st.empty()
    for i in range(seconds, 0, -1):
        placeholder.markdown(f"⏳ Time left: **{i}** seconds")
        time.sleep(1)
    placeholder.markdown("Time's up! ⏰")

# Main app
def main():
    st.title("Sports Trivia Game")

    today_str = datetime.date.today().isoformat()
    questions_text = load_questions_cache(today_str)

    if questions_text is None:
        st.info("Fetching latest sports data and generating questions...")
        data = fetch_nba_top_scorers()
        if data is None:
            st.stop()
        # Summarize the data for prompt (basic example, customize as needed)
        player_names = [p["strPlayer"] for p in data.get("player", []) if "strPlayer" in p]
        data_summary = f"Players: {', '.join(player_names[:10])} and their stats."
        questions_text = generate_trivia_questions(data_summary)
        save_questions_cache(today_str, questions_text)
    else:
        st.success("Loaded today's questions from cache.")

    questions = parse_questions(questions_text)

    score = 0
    total = len(questions)

    for idx, q in enumerate(questions):
        st.markdown(f"### Q{idx+1}: {q['question']}")
        options = q["options"]
        # Multiple choice radio buttons
        choice = st.radio("Select your answer:", options, key=f"q{idx}")
        countdown_timer(15)  # 15 seconds countdown per question
        # TODO: Add logic to check correctness once correct answers are available
        st.markdown("---")

    st.write(f"Your final score: {score} / {total}")

if __name__ == "__main__":
    main()
