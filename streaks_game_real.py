import streamlit as st
import requests
import json
import openai
import time
import os

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Please set your OPENAI_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

def fetch_nba_teams():
    url = "https://www.balldontlie.io/api/v1/teams"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        teams = data.get("data", [])
        return teams
    except Exception as e:
        st.error(f"Error fetching NBA teams: {e}")
        return []

def generate_trivia_questions(data_summary, retries=3, wait=10):
    prompt = (
        "Create 10 interesting NBA trivia questions with 4 multiple-choice answers each. "
        "Use this NBA team data:\n"
        f"{json.dumps(data_summary, indent=2)}\n"
        "Return the questions as a JSON list, each with 'question', 'choices', and 'answer'."
    )

    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1100,
                temperature=0.7,
            )
            questions_json = response.choices[0].message.content
            return json.loads(questions_json)
        except openai.error.RateLimitError:
            if attempt < retries - 1:
                st.warning(f"Rate limit reached. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                st.error("Rate limit exceeded. Please try again later.")
                return []
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            return []

@st.cache_data(ttl=86400)
def get_daily_questions(data_summary):
    return generate_trivia_questions(data_summary)

def main():
    st.title("Streaks-Style NBA Trivia Game")

    st.info("Fetching NBA teams...")
    teams = fetch_nba_teams()

    if not teams:
        st.warning("Could not retrieve NBA teams. Cannot generate questions.")
        return

    st.info("Generating trivia questions (this may take a few seconds)...")
    questions = get_daily_questions(teams)

    if not questions:
        st.warning("No trivia questions generated.")
        return

    for idx, q in enumerate(questions, start=1):
        st.write(f"**Question {idx}:** {q['question']}")
        choice = st.radio("Select your answer:", q['choices'], key=f"q{idx}")

        if st.button("Submit Answer", key=f"submit_{idx}"):
            if choice == q["answer"]:
                st.success("Correct! 🎉")
            else:
                st.error(f"Wrong. Correct answer: {q['answer']}")
        st.write("---")

if __name__ == "__main__":
    main()
