import streamlit as st
import requests
import json
import time
import os
import openai
import requests

url = "https://www.thesportsdb.com/api/v2/json/all/leagues"
api_key = st.secrets.get("SPORTSDB_API_KEY") or os.getenv("SPORTSDB_API_KEY")

headers = {
    "X-API-KEY": f"{api_key}",
    "Content-Type": "application/json"
}

# Load keys from Streamlit secrets or environment variables
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or not SPORTSDB_API_KEY:
    st.error("Please set your OPENAI_API_KEY and SPORTSDB_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

def fetch_nba_standings():
    """
    Fetch NBA standings (top teams) from TheSportsDB for the 2023-2024 season.
    Returns a list of dicts with team and standings info.
    """
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()

        if not res.text:
            st.error("No data returned from TheSportsDB API (empty response). Please check your API key and parameters.")
            return []

        data = res.json()
        if not data or "table" not in data:
            st.warning("No standings data found in API response.")
            return []

        standings = []
        for entry in data["table"][:10]:  # top 10 teams
            standings.append({
                "team": entry.get("name"),
                "position": entry.get("intRank"),
                "played": entry.get("intPlayed"),
                "win": entry.get("intWin"),
                "loss": entry.get("intLoss"),
                "points": entry.get("intPoints")
            })
        return standings
    except requests.exceptions.RequestException as e:
        st.error(f"Network/API error fetching NBA standings: {e}")
        return []
    except json.JSONDecodeError:
        st.error("Failed to parse JSON response from TheSportsDB API.")
        return []

def generate_trivia_questions(data_summary, retries=3, wait=10):
    """
    Generate 10 multiple-choice sports trivia questions using OpenAI's GPT model,
    based on provided data_summary.
    Retries on rate limits with backoff.
    """
    prompt = (
        "Generate 10 interesting sports trivia questions with 4 multiple-choice answers each. "
        "Use this NBA standings data as context for questions about teams and their performance:\n"
        f"{json.dumps(data_summary, indent=2)}\n"
        "Return the questions in JSON format as a list, each with 'question', 'choices' (list of 4), and 'answer' (correct choice)."
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
    st.title("Streaks-Style Sports Trivia Game")

    st.info("Fetching latest NBA standings...")
    data_summary = fetch_nba_standings()

    if not data_summary:
        st.warning("Could not retrieve NBA standings. Cannot generate questions.")
        return

    st.info("Generating trivia questions (this may take a few seconds)...")
    questions = get_daily_questions(data_summary)

    if not questions:
        st.warning("No trivia questions were generated.")
        return

    st.write("---")
    st.write("### Today's Trivia Questions:")

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
