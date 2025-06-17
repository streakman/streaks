import streamlit as st
import openai

# Your OpenAI API key - set this in Streamlit secrets or env vars securely
openai.api_key = st.secrets.get("openai_api_key") or "your-api-key-here"

st.title("NFL Trivia Game Powered by OpenAI")
st.write("Test your NFL knowledge with AI-generated trivia questions!")

# Hardcoded NFL teams list for demo
nfl_teams = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"
]

st.write(f"Using {len(nfl_teams)} NFL teams for trivia generation.")

num_questions = 3
st.write(f"Generating {num_questions} trivia questions, please wait...")

def generate_trivia_questions(teams, n):
    prompt = (
        f"Create {n} NFL trivia questions about the following teams: {', '.join(teams)}. "
        "Format each question as: 'Q: <question>? A: <answer>'. Only plain text, no lists."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating trivia questions:\n{e}"

trivia_output = generate_trivia_questions(nfl_teams, num_questions)
st.text_area("Trivia Questions:", value=trivia_output, height=300)
