import streamlit as st
import openai
import json
import random

# Set your OpenAI API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai_api_key"]
openai.api_key = OPENAI_API_KEY

# Hardcoded NFL teams list to avoid API-Football calls
@st.cache_data(ttl=86400)
def fetch_nfl_teams():
    st.info("[DEBUG] Using hardcoded NFL teams list")
    return [
        "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens",
        "Buffalo Bills", "Carolina Panthers", "Chicago Bears",
        "Cincinnati Bengals", "Cleveland Browns", "Dallas Cowboys",
        "Denver Broncos", "Detroit Lions", "Green Bay Packers",
        "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars",
        "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
        "Los Angeles Rams", "Miami Dolphins", "Minnesota Vikings",
        "New England Patriots", "New Orleans Saints", "New York Giants",
        "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers",
        "San Francisco 49ers", "Seattle Seahawks", "Tampa Bay Buccaneers",
        "Tennessee Titans", "Washington Commanders"
    ]

# Extract JSON safely from OpenAI output
def extract_json(response_text):
    try:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        return response_text[start:end]
    except ValueError:
        return "[]"

# Generate 3 trivia questions using OpenAI GPT-4
def generate_trivia_questions(teams_data):
    prompt = (
        "Generate 3 unique NFL trivia questions using only the following team names: "
        f"{', '.join(teams_data)}. Each question should be a dictionary with this structure: "
        "{\"question\": ..., \"choices\": [...], \"answer\": ...}. Make sure answers are accurate."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    questions_json_raw = response.choices[0].message.content
    questions_json_clean = extract_json(questions_json_raw)
    questions = json.loads(questions_json_clean)
    return questions

@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    try:
        return generate_trivia_questions(teams_data)
    except Exception as e:
        st.error(f"Error generating trivia questions: {e}")
        return []

def main():
    st.title("NFL Trivia Game Powered by OpenAI")
    st.write("Test your NFL knowledge with AI-generated trivia questions!")

    teams_data = fetch_nfl_teams()
    st.info(f"Using {len(teams_data)} NFL teams for trivia generation.")

    st.info("Generating 3 trivia questions, please wait...")
    questions = get_daily_questions(teams_data)

    if not questions:
        st.error("No trivia questions available. Try again later.")
        return

    user_answers = []

    for idx, q in enumerate(questions, 1):
        question_text = q.get("question", f"Missing question {idx}")
        choices = q.get("choices", [])
        if not isinstance(choices, list) or len(choices) != 4:
            st.error(f"Invalid choices for question {idx}. Skipping.")
            continue
        st.write(f"**Q{idx}:** {question_text}")
        choice = st.radio("Your answer:", choices, key=f"q{idx}")
        user_answers.append(choice)
        st.write("---")

    if st.button("Submit Answers"):
        score = 0
        for i, (q, a) in enumerate(zip(questions, user_answers), 1):
            correct = q.get("answer")
            if a == correct:
                score += 1
            st.markdown(f"**Q{i} Answer:** {correct}")
        st.success(f"You scored {score} / {len(questions)}!")

if __name__ == "__main__":
    main()
