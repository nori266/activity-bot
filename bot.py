from datetime import datetime
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import telebot

from db_manager.db_entities import Activity, ActivityCatalog


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


# Load activities from the database
def get_active_activities_from_db():
    # TODO .filter_by(status='active') - logic with status
    # for now just returns all the activities
    session = Session()
    active_activities = session.query(ActivityCatalog).all()
    session.close()
    return active_activities


activities = get_active_activities_from_db()


@bot.message_handler(commands=['start'])
def send_welcome(message, is_first_message=True):
    session = Session()

    # Fetch activities ordered by last_chosen in descending order
    latest_activities = session.query(ActivityCatalog).order_by(ActivityCatalog.last_chosen.desc()).limit(8).all()

    session.close()

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)

    # Create buttons based on the fetched activities
    activity_buttons = [telebot.types.KeyboardButton(f'{a.name} {a.emoji}') for a in latest_activities]

    markup.add(*activity_buttons)
    markup.add(telebot.types.KeyboardButton("More Activities"))
    if is_first_message:
        text = "Choose an activity to start tracking:"
    else:
        text = "..."
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "More Activities")
def more_activities(message):
    # TODO list activities sorted by frequency
    session = Session()
    all_activities = session.query(ActivityCatalog).all()
    session.close()

    # Create an inline keyboard markup
    markup = telebot.types.InlineKeyboardMarkup()

    # Assuming each activity has 'id' and 'name' attributes
    for activity in all_activities:
        button = telebot.types.InlineKeyboardButton(text=activity.name, callback_data=f"activity_{activity.id}")
        markup.add(button)

    # Send the markup
    bot.send_message(message.chat.id, "Select an activity:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("activity_"))
def handle_activity_callback(call):
    activity_id = call.data.split("_")[1]
    user_id = call.message.chat.id

    session = Session()
    activity = session.query(ActivityCatalog).filter_by(id=activity_id).first()
    session.close()

    if activity:
        # Mock a message object to pass to the start_or_stop_activity function
        mock_message = type('', (), {})()  # Create a simple object
        mock_message.text = activity.name
        mock_message.chat = type('', (), {})()
        mock_message.chat.id = user_id

        # Call the function
        start_or_stop_activity(mock_message)
        send_welcome(mock_message, False)

    bot.answer_callback_query(call.id)


# Define a function to retrieve activity_id by its name
def get_activity_id_by_name(name, session):
    activity = session.query(ActivityCatalog).filter(ActivityCatalog.name == name).first()
    if activity:
        return activity.id
    return None


def get_activity_name_by_id(activity_id):
    session = Session()  # Start a new session

    try:
        # Fetch the ActivityCatalog entry by its ID
        activity_entry = session.query(ActivityCatalog).filter_by(id=activity_id).first()

        if activity_entry:  # If a matching entry was found
            return activity_entry.name  # Return the name of the activity
        else:  # If no matching entry was found
            return None
    except Exception as e:
        print(f"Error fetching activity name for ID {activity_id}: {e}")
        return None
    finally:
        session.close()  # Close the session


@bot.message_handler(func=lambda message: any(a.name == activity_name_wo_emoji(message.text) for a in activities))
def start_or_stop_activity(message):
    user_id = message.chat.id
    activity_name = activity_name_wo_emoji(message.text)

    session = Session()

    # Fetch the activity_id using the name
    activity_id = get_activity_id_by_name(activity_name, session)

    if not activity_id:  # If activity is not found
        session.close()
        bot.send_message(user_id, f"Couldn't find activity: {activity_name}")
        return

    if user_id not in active_sessions:
        active_sessions[user_id] = {}

    if activity_id in active_sessions[user_id]:
        # Stop the activity
        start_time = active_sessions[user_id][activity_id]
        end_time = datetime.now()
        duration_timedelta = end_time - start_time
        duration_seconds = duration_timedelta.seconds
        formatted_duration = format_duration(duration_seconds)

        activity = Activity(user_id=user_id, activity_id=activity_id, start_time=start_time, end_time=end_time, duration=duration_seconds)
        session.add(activity)
        session.commit()

        del active_sessions[user_id][activity_id]
        bot.send_message(user_id, f"Stopped tracking {activity_name}. Duration: {formatted_duration} seconds")
    else:
        # Start the activity
        active_sessions[user_id][activity_id] = datetime.now()
        bot.send_message(user_id, f"Started tracking {activity_name}. Click again to stop.")

        # Update the last_chosen timestamp for the activity to rearrange the buttons
        chosen_activity = session.query(ActivityCatalog).filter_by(name=activity_name).first()
        if chosen_activity:
            chosen_activity.last_chosen = datetime.now()
            session.add(chosen_activity)
            session.commit()

    session.close()


@bot.message_handler(commands=['current'])
def list_current_activities(message):
    user_id = message.chat.id

    # Check if the user has any active sessions
    if user_id in active_sessions and active_sessions[user_id]:
        activities_msg = "Currently active activities:\n"
        for activity_id, start_time in active_sessions[user_id].items():
            # Note: You might want to fetch the actual activity name from the database using the activity_id.
            # For simplicity, I'm assuming you have a function called 'get_activity_name_by_id' that does this.
            activity_name = get_activity_name_by_id(activity_id)
            activities_msg += f"- {activity_name} (Started at: {start_time.strftime('%H:%M:%S')})\n"
        bot.send_message(user_id, activities_msg)
    else:
        bot.send_message(user_id, "No currently active activities.")


def format_duration(duration_seconds):
    hours, remainder = divmod(duration_seconds, 3600)
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
