import openai
import requests
import json
import streamlit as st
from datetime import date
import os

# === CONFIGURE YOUR API KEYS HERE ===
THESPORTSDB_API_KEY = "https://www.thesportsdb.com/api/v1/json/123/"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

# === Fetch recent NBA top scorers from TheSportsDB ===
def fetch_nba_top_scorers():
    url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchplayers.php?t=Los Angeles Lakers"
    res = requests.get(url)

    print("Response status code:", res.status_code)
    print("Response content:", res.text)  # <-- Add this to see what you got

    try:
        data = res.json()
    except Exception as e:
        print("JSON decode error:", e)
        return None  # Or handle it gracefully

    # rest of your code ...
    
    if not data or not data.get('player'):
        return "No recent NBA stats found."

    players = data['player'][:5]  # Take first 5 players as example

    summary = "Recent NBA players on Los Angeles Lakers: "
    for p in players:
        name = p.get('strPlayer')
        position = p.get('strPosition', 'Unknown')
        summary += f"{name} ({position}), "
    return summary.strip(", ")

# === Generate trivia questions using GPT based on recent data ===
def generate_trivia_questions(data_summary):
    prompt = f"""
You are a sports trivia question generator.

Using the following recent NBA player data:
{data_summary}

Generate 10 multiple-choice trivia questions. Each question should have 4 answer options, one correct answer, and be about NBA players, their positions, historical NBA facts, or team achievements.

Return your answer as a JSON array with this format:

[
  {{
    "question": "Question text",
    "choices": ["option1", "option2", "option3", "option4"],
    "correct": "correct option text"
  }},
  ...
]
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1100,
    )
    text = response.choices[0].message.content
    try:
        questions = json.loads(text)
    except Exception as e:
        st.error("Failed to parse questions JSON from AI.")
        st.text(text)
        questions = []
    return questions

# === Streamlit app UI ===
def main():
    st.title("Daily Sports Trivia (NBA Example)")

    today = str(date.today())
    cache_file = f"questions_{today}.json"

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            questions = json.load(f)
    else:
        st.info("Fetching recent NBA player data...")
        data_summary = fetch_nba_top_scorers()
        st.write("Data summary used to generate questions:")
        st.write(data_summary)
        st.info("Generating trivia questions via AI...")
        questions = generate_trivia_questions(data_summary)
        with open(cache_file, "w") as f:
            json.dump(questions, f)

    if not questions:
        st.error("No trivia questions available.")
        return

    score = 0
    for i, q in enumerate(questions):
        st.write(f"### Question {i+1}: {q['question']}")
        choice = st.radio("Choose an answer:", q['choices'], key=i)
        if choice:
            if choice == q['correct']:
                st.success("Correct!")
                score += 1
            else:
                st.error(f"Wrong! Correct answer: {q['correct']}")

    st.write(f"## Your score: {score} / {len(questions)}")

if __name__ == "__main__":
    main()
