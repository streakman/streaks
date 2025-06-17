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

def fetch_nba_standings():
    """
    Fetch NBA standings (Eastern Conference) from TheSportsDB API.
    """
    # TheSportsDB API endpoint for NBA standings, Eastern conference 2023 season
    url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_API_KEY}/lookuptable.php?l=4387&s=2023-2024"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "table" not in data or not data["table"]:
            st.warning("No NBA standings data found in the response.")
            return []
        
        # Extract top 10 teams with key stats
        standings = []
        for entry in data["table"][:10]:
            standings.append({
                "team": entry.get("name"),
                "position": entry.get("intRank"),
                "played": entry.get("intPlayed"),
                "win": entry.get("intWin"),
                "loss": entry.get("intLoss"),
                "points": entry.get("intPoints")
            })
        return standings
    
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error fetching NBA standings: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching NBA standings: {e}")
    except json.JSONDecodeError:
        st.error("Error parsing NBA standings JSON data.")
    return []

def generate_trivia_questions(data_summary, retries=3, wait=10):
    """
    Generate 10 sports trivia questions with OpenAI GPT-4o-mini,
    using the fetched NBA standings data as context.
    """
    prompt = (
        "Generate 10 interesting and diverse NBA trivia questions based on these team standings, "
        "with 4 multiple-choice answers each. Format the output as a JSON list, where each entry has "
        "'question' (string), 'choices' (list of 4 strings), and 'answer' (correct choice string).\n\n"
        f"NBA Standings Data:\n{json.dumps(data_summary, indent=2)}\n\n"
        "Make sure questions are engaging and test knowledge about team performance, wins, losses, and points."
    )
    
    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1100,
                temperature=0.7,
            )
            questions_text = response.choices[0].message.content
            return json.loads(questions_text)
        except openai.error.RateLimitError:
            if attempt < retries - 1:
                st.warning(f"Rate limit hit, retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                st.error("OpenAI API rate limit exceeded. Try again later.")
                return []
        except json.JSONDecodeError:
            st.error("Failed to parse questions JSON from OpenAI response.")
            return []
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
            return []
    return []

@st.cache_data(ttl=86400)
def get_daily_questions(data_summary):
    return generate_trivia_questions(data_summary)

def main():
    st.title("🏀 NBA Standings Trivia Game")

    st.info("Fetching NBA standings data...")
    data_summary = fetch_nba_standings()

    if not data_summary:
        st.warning("No NBA standings data available, cannot generate questions.")
        return

    st.info("Generating trivia questions (may take a few seconds)...")
    questions = get_daily_questions(data_summary)

    if not questions:
        st.warning("Failed to generate trivia questions.")
        return

    st.write("---")
    st.header("Today's NBA Trivia Questions")

    for i, q in enumerate(questions, start=1):
        st.write(f"**Q{i}: {q['question']}**")
        choice = st.radio("Your answer:", q["choices"], key=f"q{i}")
        if st.button("Submit Answer", key=f"submit_{i}"):
            if choice == q["answer"]:
                st.success("Correct! 🎉")
            else:
                st.error(f"Wrong! The correct answer is: {q['answer']}")
        st.write("---")

if __name__ == "__main__":
    main()
