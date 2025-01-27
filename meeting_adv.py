from flask import Flask, request, redirect
import requests
import os
import openai
from dotenv import load_dotenv
import json
import datetime
from dateutil import parser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables from .env
load_dotenv(dotenv_path=".env", override=True)

# Retrieve values from .env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN_URL = os.getenv("TOKEN_URL")
AUTH_URL = os.getenv("AUTH_URL")
SCOPES = os.getenv("SCOPES")
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def get_google_calendar_service():
    import pickle
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    credentials_path = os.getenv("GOOGLE_CREDENTIALS")  # Path to credentials.json
    token_path = "token.pickle"  # Where to save the authenticated credentials
    creds = None

    # Load credentials from token.pickle if it exists
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials are available, prompt the user to authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                ["https://www.googleapis.com/auth/calendar"]
            )
            creds = flow.run_local_server(port=8080)

        # Save the credentials for future use
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)

@app.route("/book_meeting", methods=["POST"])
def book_meeting():
    try:
        data = request.json
        natural_language_text = data.get("text", "")

        if not natural_language_text:
            return {"error": "No input provided"}, 400

        # Parse the meeting request
        meeting_details = parse_meeting_request(natural_language_text)

        # Set fixed organizer and always invite arsachde@cisco.com
        organizer_email = "archit.sachdeva007@gmail.com"
        invitees = [{"email": "arsachde@cisco.com"}] + [{"email": email} for email in meeting_details["invitees"]]

        # Static Webex meeting details
        webex_meeting_link = "https://cisco.webex.com/meet/arsachde"
        meeting_number = "1869 41 0779"
        meeting_dial = "arsachde.cisco@webex.com"
        access_code = "1869 41 0779"

        # Add the meeting to Google Calendar
        try:
            calendar_service = get_google_calendar_service()
            google_event = {
                "summary": meeting_details["title"],
                "location": webex_meeting_link,
                "description": f"""
                Join the Webex meeting using the details below:

                Meeting Link: {webex_meeting_link}
                Meeting Number: {meeting_number}
                Dial: {meeting_dial}
                Access Code: {access_code}
                """,
                "start": {
                    "dateTime": meeting_details["start"],
                    "timeZone": "Europe/London",
                },
                "end": {
                    "dateTime": meeting_details["end"],
                    "timeZone": "Europe/London",
                },
                "attendees": [{"email": "archit.sachdeva007@gmail.com"}] + invitees,
            }
            google_response = calendar_service.events().insert(
                calendarId="primary", 
                body=google_event, 
                sendUpdates="all"
            ).execute()
        except Exception as google_error:
            return {"error": "Meeting booked on Webex, but failed to add to Google Calendar."}

        return {
            "message": "Meeting successfully booked and added to Google Calendar!",
            "webex_details": {
                "meeting_link": webex_meeting_link,
                "meeting_number": meeting_number,
                "dial": meeting_dial,
                "access_code": access_code,
            },
        }

    except Exception as e:
        return {"error": str(e)}, 500

def parse_meeting_request(natural_language_text):
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
    Today is {current_date}. Parse the following text into JSON for a Webex meeting request:

    Input: "{natural_language_text}"
    JSON Format:
    {{
        "title": "Meeting Title",
        "start": "ISO 8601 Start Time (future-dated in Europe/London)",
        "end": "ISO 8601 End Time (future-dated in Europe/London, 1 hour after start time if not explicitly mentioned)",
        "invitees": ["email1@example.com", "email2@example.com"]
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )

    parsed_json = response['choices'][0]['message']['content']
    try:
        return json.loads(parsed_json)
    except json.JSONDecodeError:
        raise Exception("Failed to parse JSON response from OpenAI")

def test_google_calendar_event():
    try:
        service = get_google_calendar_service()
        event = {
            "summary": "Test Event",
            "location": "https://example.com",
            "description": "Testing Google Calendar API",
            "start": {
                "dateTime": "2025-01-27T15:00:00+00:00",
                "timeZone": "Europe/London",
            },
            "end": {
                "dateTime": "2025-01-27T16:00:00+00:00",
                "timeZone": "Europe/London",
            },
            "attendees": [{"email": "archit.sachdeva007@gmail.com"}],
        }
        response = service.events().insert(calendarId="primary", body=event).execute()
        print("Google Calendar Event Created:", response)
    except Exception as e:
        print("Google Calendar API Test Failed:", str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)