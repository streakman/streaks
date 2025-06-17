import streamlit as st
import requests
import openai
import json
import random
import time

# Set your API keys
OPENAI_API_KEY = st.secrets["openai_api_key"]
openai.api_key = OPENAI_API_KEY

# Hardcoded NFL teams list for now (avoids API-Football limits)
NFL_TEAMS = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"
]

def extract_json(response_text):
    st.info("[DEBUG] Extracting JSON from OpenAI response")
    try:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        return response_text[start:end]
    except ValueError as ve:
        st.error(f"[DEBUG] JSON extraction failed: {ve}")
        return "[]"

def generate_trivia_questions(teams_data):
    st.info("[DEBUG] Generating trivia questions")
    prompt = (
        "Generate 3 unique NFL trivia questions using only these teams: "
        f"{', '.join(teams_data)}. Each question should be a dictionary with keys: "
        "\"question\", \"choices\" (list of 4), and \"answer\". The answer must be one of the choices."
    )

    try:
        st.info("[DEBUG] Sending request to OpenAI ChatCompletion")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        st.info(f"[DEBUG] OpenAI raw response: {content[:300]}...")
        questions_json = extract_json(content)
        questions = json.loads(questions_json)
        st.info(f"[DEBUG] Parsed {len(questions)} questions successfully")
        return questions
    except openai.error.RateLimitError:
        st.warning("[DEBUG] Rate limit exceeded. Please try again later.")
        return []
    except json.JSONDecodeError as jde:
        st.error(f"[DEBUG] JSON decode error: {jde}")
        return []
    except Exception as e:
        st.error(f"[DEBUG] Unexpected error: {e}")
        return []

def main():
    st.title("NFL Trivia Game Powered by OpenAI")
    st.write("Test your NFL knowledge with AI-generated trivia questions!")

    st.info("[DEBUG] Using hardcoded NFL teams list")
    st.info(f"Using {len(NFL_TEAMS)} NFL teams for trivia generation.")

    st.info("Generating 3 trivia questions, please wait...")
    questions = generate_trivia_questions(NFL_TEAMS)

    if not questions:
        st.error("No trivia questions available. Try again later.")
        return

    st.markdown("### Today's NFL Trivia Questions")
    user_answers = []

    if not isinstance(questions, list):
        st.error("Failed to generate valid trivia questions.")
        return

    for idx, q in enumerate(questions, 1):
        try:
            question_text = q.get("question", f"Missing question {idx}")
            choices = q.get("choices", [])
            if not isinstance(choices, list) or len(choices) != 4:
                raise ValueError("Invalid choices format.")
            st.write(f"**Q{idx}:** {question_text}")
            choice = st.radio("Your answer:", choices, key=f"q{idx}")
            user_answers.append(choice)
            st.write("---")
        except Exception as e:
            st.error(f"Error rendering question {idx}: {e}")
            user_answers.append(None)

    if st.button("Submit Answers"):
        st.info("[DEBUG] Submit clicked")
        score = 0
        for i, (q, a) in enumerate(zip(questions, user_answers), 1):
            correct = q.get("answer")
            if a == correct:
                score += 1
            st.markdown(f"**Q{i} Answer:** {correct}")
        st.success(f"You scored {score} / {len(questions)}!")

if __name__ == "__main__":
    main()
