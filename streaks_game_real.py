import streamlit as st
from datetime import datetime
import json
import os
import random
import time

# Sportsipy imports for different sports
from sportsipy.nba.schedule import Schedule as NBASchedule
from sportsipy.mlb.schedule import Schedule as MLBSchedule
from sportsipy.nhl.schedule import Schedule as NHLSchedule
from sportsipy.nfl.schedule import Schedule as NFLSchedule

st.set_page_config(page_title="Multi-Sport Streaks Game", page_icon="🏆")

NUM_QUESTIONS = 10
TIME_PER_QUESTION = 20  # seconds per question
USER_DIR = "users"
os.makedirs(USER_DIR, exist_ok=True)

SPORTS = {
    "NBA": {
        "schedule": NBASchedule,
        "teams": ["Lakers", "Warriors", "Celtics", "Bulls", "Nets", "Heat", "Suns", "Knicks"]
    },
    "MLB": {
        "schedule": MLBSchedule,
        "teams": ["Yankees", "Red Sox", "Dodgers", "Giants", "Cubs", "Mets", "Phillies", "Cardinals"]
    },
    "NHL": {
        "schedule": NHLSchedule,
        "teams": ["Canadiens", "Maple Leafs", "Blackhawks", "Bruins", "Rangers", "Flyers", "Penguins", "Capitals"]
    },
    "NFL": {
        "schedule": NFLSchedule,
        "teams": ["Patriots", "Cowboys", "Packers", "Steelers", "Chiefs", "Seahawks", "Rams", "Giants"]
    }
}

# --- User Login ---
USER = st.text_input("Enter your username:", key="username").strip()
if not USER:
    st.warning("Please enter your username to start playing.")
    st.stop()

DATA_FILE = os.path.join(USER_DIR, f"{USER}.json")
TODAY = datetime.now().strftime("%Y-%m-%d")

def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "history": {},  # date -> {questions: [], answers: [], completed: bool}
            "current_streak": 0,
            "longest_streak": 0,
        }

def save_user_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_user_data()

def fetch_games_for_sport(sport_name, schedule_class, teams):
    try:
        # Pick a random team from this sport
        team = random.choice(teams)
        schedule = schedule_class(team)
        today_str = TODAY
        games_today = [g for g in schedule if g.date.strftime("%Y-%m-%d") == today_str]
        questions = []
        for game in games_today:
            # question text, correct answer, all teams
            question_text = f"In {sport_name}, who will win the game: {team} vs {game.opponent_name}?"
            correct_answer = random.choice([team, game.opponent_name])
            # choices include correct answer + 3 random other teams from same sport (not duplicates)
            choices = set([correct_answer])
            while len(choices) < 4:
                choices.add(random.choice(teams))
            choices = list(choices)
            random.shuffle(choices)
            questions.append({
                "question": question_text,
                "correct": correct_answer,
                "choices": choices
            })
        return questions
    except Exception as e:
        st.warning(f"Failed fetching {sport_name} data: {e}")
        return []

def get_mixed_questions():
    all_questions = []
    sports_list = list(SPORTS.keys())
    while len(all_questions) < NUM_QUESTIONS:
        sport_name = random.choice(sports_list)
        qlist = fetch_games_for_sport(sport_name,
                                      SPORTS[sport_name]["schedule"],
                                      SPORTS[sport_name]["teams"])
        if not qlist:
            # Fallback random question
            sport = sport_name
            teams = SPORTS[sport]["teams"]
            t1, t2 = random.sample(teams, 2)
            question_text = f"In {sport}, who will win the game: {t1} vs {t2}?"
            correct = random.choice([t1, t2])
            choices = [correct]
            while len(choices) < 4:
                choice = random.choice(teams)
                if choice not in choices:
                    choices.append(choice)
            random.shuffle(choices)
            all_questions.append({
                "question": question_text,
                "correct": correct,
                "choices": choices
            })
        else:
            all_questions.extend(qlist)

    return all_questions[:NUM_QUESTIONS]

if TODAY not in data["history"]:
    data["history"][TODAY] = {
        "questions": get_mixed_questions(),
        "answers": [],
        "completed": False,
    }
    save_user_data(data)

today_data = data["history"][TODAY]

st.title("🏆 Multi-Sport Streaks Game")
st.write(f"User: **{USER}**")
st.write(f"Date: {TODAY}")
st.markdown("---")

if today_data["completed"]:
    st.success("✅ You've already completed today's questions!")
    score = sum(today_data["answers"])
    st.write(f"Your score: {score} / {NUM_QUESTIONS}")
    st.write(f"Current streak: {data['current_streak']}")
    st.write(f"Longest streak: {data['longest_streak']}")
else:
    st.write(f"Answer the {NUM_QUESTIONS} questions below. You have {TIME_PER_QUESTION} seconds for each.")

    answers = []
    for i, q in enumerate(today_data["questions"]):
        st.write(f"**Q{i+1}:** {q['question']}")
        timer_placeholder = st.empty()
        start_time = time.time()
        user_answer = None

        # Show choices as buttons
        cols = st.columns(4)
        answered = False
        while not answered:
            elapsed = int(time.time() - start_time)
            time_left = TIME_PER_QUESTION - elapsed
            if time_left <= 0:
                timer_placeholder.markdown(f"⏰ Time's up! Moving to next question.")
                break
            timer_placeholder.markdown(f"⏳ Time left: {time_left}s")

            for idx, choice in enumerate(q['choices']):
                if cols[idx].button(choice, key=f"q{i}_choice{idx}"):
                    user_answer = choice
                    answered = True
                    break

            time.sleep(0.1)

        timer_placeholder.empty()

        if user_answer is None:
            st.write("No answer given. Marked as incorrect.")
            answers.append(0)
        else:
            if user_answer == q['correct']:
                st.success("Correct! 🎉")
                answers.append(1)
            else:
                st.error(f"Incorrect. Correct answer was: {q['correct']}")
                answers.append(0)

    today_data["answers"] = answers
    today_data["completed"] = True
    score = sum(answers)

    if score == NUM_QUESTIONS:
        data["current_streak"] += 1
        st.balloons()
        st.success(f"Perfect! Your streak is now {data['current_streak']}")
    else:
        data["current_streak"] = 0
        st.warning(f"Your score was {score}. Streak reset to 0.")

    if data["current_streak"] > data["longest_streak"]:
        data["longest_streak"] = data["current_streak"]

    save_user_data(data)

st.sidebar.header("📊 Your Stats")
st.sidebar.write(f"Current streak: {data['current_streak']}")
st.sidebar.write(f"Longest streak: {data['longest_streak']}")
st.sidebar.write(f"Days played: {len(data['history'])}")
