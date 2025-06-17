import streamlit as st
import requests
import json
import time
import os
import openai

# Load keys from Streamlit secrets or environment variables
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
SPORTSDB_API_KEY = st.secrets.get("SPORTSDB_API_KEY") or os.getenv("SPORTSDB_API_KEY")

if not OPENAI_API_KEY or not SPORTSDB_API_KEY:
    st.error("Please set your OPENAI_API_KEY and SPORTSDB_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY

# Example fetch function: Get NBA top scorers from TheSportsDB
def fetch_nba_top_scorers():
    url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_API_KEY}/lookuptable.php?l=4387&s=2024"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        # Extract relevant data for prompt, e.g., top 5 scorers
        scorers = []
        if "table" in data:
            for entry in data["table"][:5]:
                scorers.append({
                    "name": entry.get("strPlayer"),
                    "team": entry.get("name_team"),
                    "goals": entry.get("intGoals"),
                    "assists": entry.get("intAssists"),
                })
        return scorers
    except Exception as e:
        st.error(f"Error fetching NBA data: {e}")
        return []

# Generate trivia questions via OpenAI, with retry & backoff
def generate_trivia_questions(data_summary, retries=3, wait=10):
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

    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1100,
                temperature=0.8,
            )
            questions_json = response.choices[0].message.content
            return json.loads(questions_json)
        except openai.error.RateLimitError:
            if attempt < retries - 1:
                st.warning(f"Rate limit hit, retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                st.error("Rate limit exceeded. Please try again later.")
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            break
    return []

# Cache daily questions to avoid multiple OpenAI calls per day
@st.cache_data(ttl=86400)
def get_today_questions(data_summary):
    return generate_trivia_questions(data_summary)

# Main app function
def main():
    st.title("Streaks-Style Sports Trivia Game")

    st.write("Fetching latest sports data...")
    data_summary = fetch_nba_top_scorers()

    if not data_summary:
        st.warning("No data available to generate questions.")
        return

    st.write("Generating questions...")
    questions = get_today_questions(data_summary)

    if not questions:
        st.warning("No questions generated.")
        return

    # Show questions one by one with timer & choices
    for i, q in enumerate(questions, 1):
        st.write(f"### Question {i}: {q['question']}")
        choice = st.radio("Choose an answer:", q['choices'], key=i)

        if st.button("Submit answer", key=f"submit_{i}"):
            if choice == q['answer']:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. The right answer is: {q['answer']}")
            st.write("---")

if __name__ == "__main__":
    main()
