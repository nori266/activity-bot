import csv
from datetime import datetime
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import telebot

from db_manager.db_entities import Activity


load_dotenv()

# Database setup
DB_URL = os.environ.get('DB_URL')
DB_HOST = os.environ.get('DB_HOST')
engine = create_engine(
            DB_URL,
            connect_args=dict(host=DB_HOST, port=3306)
        )
Session = sessionmaker(bind=engine)


TOKEN = os.environ.get('bot_token')
bot = telebot.TeleBot(TOKEN)

active_sessions = {}  # To store start time of an activity by user

activity_log_file = "activity_logs.csv"


def csv_to_dict(filename):
    activities = []
    with open(filename, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            activities.append(row)
    return activities


activities = csv_to_dict("activities_list.csv")  # TODO to a separate table


@bot.message_handler(commands=['start'])
def send_welcome(message):

    # Filter activities with status 'active'
    active_activities = [a for a in activities if a['status'] == 'active']

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    # TODO most popular activities instead of just first
    activity_buttons = [telebot.types.KeyboardButton(f'{a["name"]} {a["emoji"]}') for a in
                        active_activities[:6]]  # Take the first 6 active activities
    markup.add(*activity_buttons)
    markup.add(telebot.types.KeyboardButton("More Activities"))
    bot.send_message(message.chat.id, "Choose an activity to start tracking:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "More Activities")
def more_activities(message):
    # Here, you can add a more advanced UI, like InlineKeyboard with a dropdown for all 30 activities
    pass


@bot.message_handler(func=lambda message: any(a["name"] == activity_name_wo_emoji(message.text) for a in activities))
def start_or_stop_activity(message):
    user_id = message.chat.id
    activity_name = activity_name_wo_emoji(message.text)

    session = Session()

    if user_id not in active_sessions:
        active_sessions[user_id] = {}

    if activity_name in active_sessions[user_id]:
        # Stop the activity
        start_time = active_sessions[user_id][activity_name]
        end_time = datetime.now()
        duration_timedelta = end_time - start_time
        duration_seconds = duration_timedelta.seconds

        activity = Activity(user_id=user_id, activity=activity_name, start_time=start_time, end_time=end_time, duration=duration_seconds)
        session.add(activity)
        session.commit()

        del active_sessions[user_id][activity_name]
        bot.send_message(user_id, f"Stopped tracking {activity_name}. Duration: {duration_seconds} seconds")
    else:
        # Start the activity
        active_sessions[user_id][activity_name] = datetime.now()
        bot.send_message(user_id, f"Started tracking {activity_name}. Click again to stop.")

    session.close()


def csv_to_dict(filename):
    activities = []

    with open(filename, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            activities.append(row)

    return activities


def format_duration(duration):
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the duration as "hours:minutes:seconds"
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def activity_name_wo_emoji(name: str):
    return name.split(' ')[0]


if __name__ == '__main__':
    if not os.path.exists(activity_log_file):
        with open(activity_log_file, "w") as f:
            f.write("user_id,activity,start_time,end_time,duration\n")  # Header

    bot.polling(none_stop=True)
