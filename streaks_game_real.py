import streamlit as st
import openai
import json
from openai.error import RateLimitError

OPENAI_API_KEY = st.secrets.get("openai_api_key")
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found in secrets!")
    st.stop()

openai.api_key = OPENAI_API_KEY

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

def extract_json(text):
    try:
        start = text.index("[")
        end = text.rindex("]") + 1
        return text[start:end]
    except ValueError:
        return "[]"

def generate_trivia_questions(teams, num=3):
    prompt = (
        f"Generate {num} unique NFL trivia questions using only the following team names: "
        f"{', '.join(teams)}. Each question should be a dictionary with this structure: "
        '{"question": ..., "choices": [...], "answer": ...}. Make sure answers are accurate.'
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        content = response.choices[0].message.content
        json_str = extract_json(content)
        questions = json.loads(json_str)
        return questions
    except RateLimitError:
        st.warning("Rate limit reached, please try again later.")
        return []
    except json.JSONDecodeError:
        st.error("Failed to decode JSON from OpenAI response.")
        return []
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []

def main():
    st.title("NFL Trivia Game Powered by OpenAI")
    st.write("Test your NFL knowledge with AI-generated trivia questions!")

    st.info("[DEBUG] Using hardcoded NFL teams list")
    st.write(f"Using {len(NFL_TEAMS)} NFL teams for trivia generation.")

    st.info(f"Generating 3 trivia questions, please wait...")
    questions = generate_trivia_questions(NFL_TEAMS, num=3)

    if not questions:
        st.error("No trivia questions available. Try again later.")
        return

    user_answers = []
    for i, q in enumerate(questions, 1):
        question = q.get("question", f"Question {i} missing")
        choices = q.get("choices", [])
        if not isinstance(choices, list) or len(choices) != 4:
            st.error(f"Invalid choices format for question {i}.")
            choices = ["N/A"] * 4

        st.write(f"**Q{i}:** {question}")
        answer = st.radio("Your answer:", choices, key=f"q{i}")
        user_answers.append(answer)
        st.write("---")

    if st.button("Submit Answers"):
        score = 0
        for i, (q, a) in enumerate(zip(questions, user_answers), 1):
            correct = q.get("answer")
            if a == correct:
                score += 1
            st.markdown(f"**Q{i} Correct Answer:** {correct}")
        st.success(f"Your score: {score} / {len(questions)}")

if __name__ == "__main__":
    main()
