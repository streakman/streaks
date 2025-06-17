import streamlit as st
import requests
import json
import time
import os
import openai

# Load keys
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
API_SPORTS_API_KEY = st.secrets.get("API_SPORTS_API_KEY") or os.getenv("API_SPORTS_API_KEY")

if not OPENAI_API_KEY or not API_SPORTS_API_KEY:
    st.error("Please set your OPENAI_API_KEY and API_SPORTS_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

# API-SPORTS NBA teams endpoint
def fetch_nba_teams():
    url = "https://api-basketball.p.rapidapi.com/teams"
    headers = {
        "X-RapidAPI-Key": API_SPORTS_API_KEY,
        "X-RapidAPI-Host": "api-basketball.p.rapidapi.com"
    }
    params = {
        "league": "12",  # NBA league ID in API-SPORTS
        "season": "2023"
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        # data['response'] contains list of teams
        teams = data.get("response", [])
        return teams
    except Exception as e:
        st.error(f"Error fetching NBA teams from API-SPORTS: {e}")
        return []

def generate_trivia_questions(teams_data, retries=3, wait=10):
    prompt = (
        "Create 10 interesting NBA multiple-choice trivia questions using the following team data:\n"
        f"{json.dumps(teams_data, indent=2)}\n"
        "Return a JSON list of questions, each with 'question', 'choices' (4 options), and 'answer'."
    )
    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1100,
                temperature=0.7,
            )
            questions_json = response.choices[0].message.content
            return json.loads(questions_json)
        except openai.error.RateLimitError:
            if attempt < retries - 1:
                st.warning(f"Rate limit hit. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                st.error("Rate limit exceeded. Please try again later.")
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            break
    return []

@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    return generate_trivia_questions(teams_data)

def main():
    st.title("NBA Trivia with API-SPORTS & OpenAI")

    st.info("Fetching NBA teams data...")
    teams = fetch_nba_teams()

    if not teams:
        st.warning("No NBA teams data available.")
        return

    st.info("Generating trivia questions (this may take a few seconds)...")
    questions = get_daily_questions(teams)

    if not questions:
        st.warning("No questions generated.")
        return

    st.write("---")
    st.write("### Today's NBA Trivia Questions:")

    for idx, q in enumerate(questions, start=1):
        st.write(f"**Question {idx}:** {q['question']}")
        choice = st.radio("Select your answer:", q['choices'], key=f"q{idx}")

        if st.button("Submit Answer", key=f"submit_{idx}"):
            if choice == q["answer"]:
                st.success("Correct! 🎉")
            else:
                st.error(f"Wrong. The correct answer is: {q['answer']}")
        st.write("---")

if __name__ == "__main__":
    main()
