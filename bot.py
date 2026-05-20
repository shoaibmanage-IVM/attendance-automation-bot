from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Slack App
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Google Sheets Authentication
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open(
    os.environ["GOOGLE_SHEET_NAME"]
).worksheet("Raw Slack Import")

print("Attendance Bot Running...")

# Attendance Message Handler
@app.event("message")
def handle_message(body, say):

    event = body.get("event", {})

    # Ignore bot messages
    if "bot_id" in event:
        return

    text = event.get("text", "")
    user = event.get("user", "Unknown")

    print("MESSAGE:", text)

    attendance_keywords = [
        "Time in",
        "Time out",
        "break",
        "personal",
        "rest"
    ]

    if not any(keyword.lower() in text.lower() for keyword in attendance_keywords):
        return

    now = datetime.now()

    record_id = str(uuid.uuid4())[:8]

    date = now.strftime("%Y-%m-%d")
    day = now.strftime("%A")
    time = now.strftime("%I:%M %p")
    full_timestamp = now.strftime("%Y-%m-%d %I:%M:%S %p")

    action = ""

    lower_text = text.lower()

    if "time in" in lower_text and "break" not in lower_text:
        action = "Starting Work"

    elif "time out" in lower_text and "break" not in lower_text:
        action = "Leaving Work"

    elif "break" in lower_text and "time out" in lower_text:
        action = "Lunch Break Start"

    elif "break" in lower_text and "time in" in lower_text:
        action = "Back From Lunch"

    elif "personal" in lower_text and "time out" in lower_text:
        action = "Personal Work Out"

    elif "personal" in lower_text and "time in" in lower_text:
        action = "Back From Personal Work"

    elif "rest" in lower_text and "time out" in lower_text:
        action = "Rest Start"

    elif "rest" in lower_text and "time in" in lower_text:
        action = "Back From Rest"

    # Add Row to Google Sheet
    sheet.append_row([
        record_id,
        date,
        day,
        user,
        user,
        "Attendance",
        action,
        text,
        time,
        full_timestamp,
        "",
        ""
    ])

    print("Attendance Added To Google Sheet")

# Start Slack Bot
if __name__ == "__main__":

    handler = SocketModeHandler(
        app,
        os.environ["SLACK_APP_TOKEN"]
    )

    handler.start()