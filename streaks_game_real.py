import streamlit as st
import openai
import json
import time
from openai.error import RateLimitError

# Set your OpenAI API key here or via Streamlit secrets
OPENAI_API_KEY = st.secrets.get("openai_api_key", None)
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found in secrets!")
    st.stop()
openai.api_key = OPENAI_API_KEY

# Hardcoded NFL teams list (to avoid API-Football rate limits)
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
    try:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        return response_text[start:end]
    except ValueError:
        return "[]"

def generate_trivia_questions(teams_data, num_questions=3):
    prompt = (
        "Generate {} unique NFL trivia questions using only the following team names: {}. "
        "Each question should be a dictionary with this structure: "
        "{\"question\": ..., \"choices\": [...], \"answer\": ...}. Make sure answers are accurate."
    ).format(num_questions, ", ".join(teams_data))

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        questions_json_raw = response.choices[0].message.content
        questions_json_clean = extract_json(questions_json_raw)
        questions = json.loads(questions_json_clean)
        return questions
    except RateLimitError:
        st.warning("OpenAI rate limit reached. Please try again later.")
        return []
    except json.JSONDecodeError:
        st.error("Failed to decode trivia questions from OpenAI response.")
        return []
    except Exception as e:
        st.error(f"Unexpected error generating trivia: {e}")
        return []

def main():
    st.title("NFL Trivia Game Powered by OpenAI")
    st.write("Test your NFL knowledge with AI-generated trivia questions!")

    st.info("[DEBUG] Using hardcoded NFL teams list")
    st.write(f"Using {len(NFL_TEAMS)} NFL teams for trivia generation.")

    st.info("Generating 3 trivia questions, please wait...")
    questions = generate_trivia_questions(NFL_TEAMS, num_questions=3)

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
                st.error(f"Invalid choices format for question {idx}.")
                choices = ["N/A", "N/A", "N/A", "N/A"]
            st.write(f"**Q{idx}:** {question_text}")
            choice = st.radio("Your answer:", choices, key=f"q{idx}")
            user_answers.append(choice)
            st.write("---")
        except Exception as e:
            st.error(f"Error rendering question {idx}: {e}")
            user_answers.append(None)

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
