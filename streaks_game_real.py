import streamlit as st
import requests
import openai
import json
import time
from openai.error import RateLimitError

# Set your API keys
API_FOOTBALL_KEY = st.secrets["api_football_key"]
OPENAI_API_KEY = st.secrets["openai_api_key"]
openai.api_key = OPENAI_API_KEY

# Fetch NFL teams from API-Football (league=1, season=2023)
@st.cache_data(ttl=86400)
def fetch_nfl_teams():
    st.info("[DEBUG] Entered fetch_nfl_teams")
    url = "https://v3.football.api-sports.io/teams?league=1&season=2023"  # NFL league ID
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    response = requests.get(url, headers=headers)
    st.info(f"[DEBUG] API response status: {response.status_code}")
    if response.status_code != 200:
        st.error(f"API error: {response.json()}")
        return []
    teams = response.json().get("response", [])
    team_names = [team["team"]["name"] for team in teams]
    st.info(f"[DEBUG] Retrieved {len(team_names)} teams")
    return team_names

def extract_json(response_text):
    st.info("[DEBUG] Entered extract_json")
    try:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        st.info("[DEBUG] Successfully extracted JSON from response")
        return response_text[start:end]
    except ValueError as ve:
        st.error(f"[DEBUG] ValueError in extract_json: {ve}")
        return "[]"

def generate_trivia_questions(teams_data):
    st.info("[DEBUG] Entered generate_trivia_questions")
    prompt = (
        "Generate 3 unique NFL trivia questions using only the following team names: "
        f"{', '.join(teams_data)}. Each question should be a dictionary with this structure: "
        "{\"question\": ..., \"choices\": [...], \"answer\": ...}. Make sure answers are accurate."
    )

    try:
        st.info("[DEBUG] Sending prompt to OpenAI")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        st.info("[DEBUG] OpenAI response received")
        questions_json_raw = response.choices[0].message.content
        st.info(f"[DEBUG] Raw response: {questions_json_raw[:200]}...")
        questions_json_clean = extract_json(questions_json_raw)
        questions = json.loads(questions_json_clean)
        st.info(f"[DEBUG] Parsed {len(questions)} questions")
        return questions
    except RateLimitError:
        st.warning("[DEBUG] RateLimitError caught")
        raise
    except json.JSONDecodeError as jde:
        st.error(f"[DEBUG] JSONDecodeError caught: {jde}")
        raise
    except Exception as e:
        st.error(f"[DEBUG] General Exception in generate_trivia_questions: {e}")
        raise

@st.cache_data(ttl=86400)
def get_daily_questions(teams_data):
    st.info("[DEBUG] Entered get_daily_questions")
    retries = 3
    for attempt in range(retries):
        st.info(f"[DEBUG] Attempt {attempt + 1} of {retries}")
        try:
            questions = generate_trivia_questions(teams_data)
            st.info(f"[DEBUG] get_daily_questions returning {len(questions)} questions")
            return questions
        except RateLimitError:
            wait = 5 + attempt * 5
            st.warning(f"Rate limit hit. Retrying in {wait} seconds...")
            time.sleep(wait)
        except json.JSONDecodeError as jde:
            st.error(f"[DEBUG] JSONDecodeError on attempt {attempt + 1}: {jde}")
            return []
        except Exception as e:
            st.error(f"[DEBUG] General Exception on attempt {attempt + 1}: {e}")
            return []
    return []

def main():
    st.title("NFL Trivia Game Powered by OpenAI")
    st.write("\nTest your NFL knowledge with AI-generated trivia questions!")

    st.info("Fetching NFL teams data from API-Football...")
    teams_data = fetch_nfl_teams()
    if not teams_data:
        st.error("No NFL teams data available. Cannot generate trivia.")
        return

    st.info(f"Using {len(teams_data)} NFL teams for trivia generation.")

    st.info("Generating 3 trivia questions, please wait...")
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
            st.info(f"[DEBUG] Processing question index {idx}")
            question_text = q.get("question", f"Missing question {idx}")
            choices = q.get("choices", [])
            st.info(f"[DEBUG] Question {idx}: {question_text}")
            st.info(f"[DEBUG] Choices: {choices}")
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
        st.info("[DEBUG] Submit button clicked")
        score = 0
        for i, (q, a) in enumerate(zip(questions, user_answers), 1):
            try:
                correct = q.get("answer")
                if a == correct:
                    score += 1
                st.markdown(f"**Q{i} Answer:** {correct}")
            except Exception as e:
                st.error(f"Could not show answer for Q{i}: {e}")
        st.success(f"You scored {score} / {len(questions)}!")

if __name__ == "__main__":
    main()
