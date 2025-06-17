import streamlit as st
import requests
import openai
import json
import random
import time
from openai.error import RateLimitError

# Set your API keys
API_FOOTBALL_KEY = st.secrets["api_football_key"]
OPENAI_API_KEY = st.secrets["openai_api_key"]
openai.api_key = OPENAI_API_KEY

# Fetch NFL teams from API-Football
@st.cache_data(ttl=86400)
def fetch_nfl_teams():
    url = "https://v3.football.api-sports.io/teams?league=1&season=2023"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception("Failed to fetch teams data.")
    teams = response.json()["response"]
    return [team["team"]["name"] for team in teams]

# Clean and extract JSON from OpenAI output
def extract_json(response_text):
    try:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        return response_text[start:end]
    except ValueError:
        return "[]"

# Generate trivia questions using OpenAI
def generate_trivia_questions(teams_data):
    prompt = (
        "Generate 10 unique NFL trivia questions using only the following team names: "
        f"{', '.join(teams_data)}. Each question should be a dictionary with this structure: "
        "{\"question\": ..., \"choices\": [...], \"answer\": ...}. Make sure answers are accurate."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        questions_json_raw = response.choices[0].message.content
        questions_json_clean = extract_json(questions_json_raw)
        return json.loads(questions_json_clean)
    except RateLimitError:
        raise
    except json.JSONDecodeError as e:
        st.error("Failed to parse trivia questions from OpenAI.")
        return []
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return []

# Retry wrapper
@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    retries = 3
    for attempt in range(retries):
        try:
            return generate_trivia_questions(teams_data)
        except RateLimitError:
            wait = 5 + attempt * 5
            st.warning(f"Rate limit hit. Retrying in {wait} seconds...")
            time.sleep(wait)
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return []
    return []

# Streamlit app

def main():
    st.title("NFL Trivia Game Powered by API-Football & OpenAI")
    st.write("\nTest your NFL knowledge with AI-generated trivia questions updated daily!")

    st.info("Fetching NFL teams data from API-Football...")
    try:
        teams_data = fetch_nfl_teams()
    except Exception as e:
        st.error(f"Error fetching NFL teams: {e}")
        return

    st.info("Generating trivia questions, please wait...")
    questions = get_daily_questions(teams_data)

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
        score = 0
        for q, a in zip(questions, user_answers):
            correct = q.get("answer")
            if a == correct:
                score += 1
        st.success(f"You scored {score} / {len(questions)}!")
        for i, q in enumerate(questions, 1):
            try:
                st.markdown(f"**Q{i} Answer:** {q['answer']}")
            except Exception as e:
                st.error(f"Could not show answer for Q{i}: {e}")

if __name__ == "__main__":
    main()
