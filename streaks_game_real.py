import os
import requests
import json
import random
import streamlit as st
from datetime import date
import openai

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")

openai.api_key = OPENAI_API_KEY

# Constants
NUM_QUESTIONS = 10
STATS_FILE = "player_stats.json"


def fetch_nba_top_scorers():
    # Example: fetch NBA top scorers of current season from TheSportsDB
    # Correct URL format:
    url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/lookup_all_players.php?id=134860"  # NBA Team ID example: Lakers = 134860
    res = requests.get(url)
    if res.status_code != 200:
        st.error(f"Error fetching NBA data: {res.status_code}")
        return []
    data = res.json()
    players = data.get("player", [])
    # Filter players with scoring info if available (or just return top 20 random players)
    return random.sample(players, min(20, len(players))) if players else []


def generate_trivia_questions(data_summary):
    # Prepare prompt for OpenAI with raw data_summary (list of player dicts)
    prompt = (
        "Create 10 interesting sports trivia questions with 4 multiple-choice answers each. "
        "Use the following player data from various sports including NBA, NFL, MLB, etc., "
        "based on their historical stats and accolades. Format as a JSON list of questions, each "
        "with 'question', 'choices' (list of 4 strings), and 'answer' (correct choice string).\n\n"
        f"Player data: {json.dumps(data_summary)}\n\n"
        "Example output:\n"
        "[\n"
        "  {\n"
        "    \"question\": \"Which NBA player scored the most points in the 2023 season?\",\n"
        "    \"choices\": [\"Player A\", \"Player B\", \"Player C\", \"Player D\"],\n"
        "    \"answer\": \"Player A\"\n"
        "  },\n"
        "  ...\n"
        "]"
    )
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1100,
        temperature=0.8,
    )
    text = response.choices[0].message.content
    try:
        questions = json.loads(text)
        if isinstance(questions, list):
            return questions
    except Exception as e:
        st.error(f"Failed to parse questions from OpenAI response: {e}")
    return []


def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def main():
    st.title("Daily Sports Trivia Streaks")

    stats = load_stats()
    today = str(date.today())
    user = st.text_input("Enter your name to start playing:", key="user_name").strip()
    if not user:
        st.info("Please enter your name to begin.")
        return

    user_stats = stats.get(user, {})
    if user_stats.get("last_played") == today:
        st.write(f"Welcome back, {user}! You have already played today.")
        st.write(f"Your current streak is: {user_stats.get('streak', 0)}")
        return

    with st.spinner("Fetching sports data..."):
        data_summary = fetch_nba_top_scorers()

    if not data_summary:
        st.error("Could not fetch sports data to generate questions. Try again later.")
        return

    with st.spinner("Generating today's questions..."):
        questions = generate_trivia_questions(data_summary)

    if not questions:
        st.error("Failed to generate questions. Please try again later.")
        return

    correct_answers = 0

    for i, q in enumerate(questions, 1):
        st.markdown(f"### Question {i}:")
        st.write(q["question"])
        choices = q["choices"]
        user_choice = st.radio("Select your answer:", choices, key=f"q{i}")

        if st.button("Submit Answer", key=f"submit_{i}"):
            if user_choice == q["answer"]:
                st.success("Correct!")
                correct_answers += 1
            else:
                st.error(f"Wrong! Correct answer: {q['answer']}")

    st.write(f"Your total correct answers today: {correct_answers} out of {NUM_QUESTIONS}")

    # Update stats
    streak = user_stats.get("streak", 0)
    if correct_answers >= 7:  # example threshold for a win streak
        streak += 1
        st.balloons()
    else:
        streak = 0

    stats[user] = {
        "last_played": today,
        "streak": streak,
        "last_score": correct_answers,
    }
    save_stats(stats)
    st.write(f"Your current winning streak: {streak}")


if __name__ == "__main__":
    main()
