from flask import Flask, request, redirect
import requests
import os
import openai
from dotenv import load_dotenv
import json
import datetime
from dateutil import parser

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

print(f"Loaded REDIRECT_URI: {REDIRECT_URI}")

app = Flask(__name__)

@app.route("/")
def home():
    return f"<a href='{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPES}&state=set_state_here'>Click here to authenticate with Webex</a>"

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Authorization failed or denied."

    # Token exchange logic (already in your code)
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_info = response.json()
        return f"Access Token: {token_info['access_token']}<br>Refresh Token: {token_info['refresh_token']}"
    else:
        return f"Failed to get access token: {response.text}"

def refresh_access_token():
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": os.getenv("REFRESH_TOKEN"),
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_info = response.json()
        # Update tokens in the environment
        os.environ["ACCESS_TOKEN"] = token_info["access_token"]
        os.environ["REFRESH_TOKEN"] = token_info["refresh_token"]
        # Save updated tokens to .env file
        with open(".env", "r") as file:
            lines = file.readlines()
        with open(".env", "w") as file:
            for line in lines:
                if line.startswith("ACCESS_TOKEN"):
                    file.write(f"ACCESS_TOKEN={token_info['access_token']}\n")
                elif line.startswith("REFRESH_TOKEN"):
                    file.write(f"REFRESH_TOKEN={token_info['refresh_token']}\n")
                else:
                    file.write(line)
        return token_info["access_token"]
    else:
        raise Exception(f"Failed to refresh token: {response.text}")

@app.route("/send_message")
def send_message():
    try:
        access_token = os.getenv("ACCESS_TOKEN")
        if not access_token:
            access_token = refresh_access_token()
    except Exception as e:
        return f"Failed to refresh access token: {e}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "roomId": os.getenv("ROOM_ID"),  # Pull the room ID from .env
        "text": "Hello from Donna V2!",
    }
    response = requests.post("https://webexapis.com/v1/messages", headers=headers, json=data)
    return f"Message sent! Response: {response.json()}"


@app.route("/book_meeting", methods=["POST"])
def book_meeting():
    try:
        # Extract natural language input from the request
        data = request.json
        natural_language_text = data.get("text", "")
        
        if not natural_language_text:
            return {"error": "No input provided"}, 400
        
        # Parse the natural language input using OpenAI
        meeting_details = parse_meeting_request(natural_language_text)

        # Debug log for meeting details
        print(f"Parsed meeting details: {meeting_details}")

        # Validate and adjust times
        now = datetime.datetime.now(datetime.timezone.utc)  # UTC timezone-aware
        # Validate and adjust times
        start_time = parser.isoparse(meeting_details["start"])
        end_time = parser.isoparse(meeting_details.get("end", ""))

        if not end_time:
            end_time = start_time + datetime.timedelta(hours=1)  # Default to 1-hour duration if not provided

        # Debug log for times
        print(f"Current UTC time: {now}")
        print(f"Start time from OpenAI: {start_time}")
        print(f"End time from OpenAI: {end_time}")

        if start_time <= now:
            return {"error": "Start time must be in the future"}, 400
        if end_time <= start_time:
            return {"error": "End time must be after start time"}, 400
        
        # Prepare Webex payload
        access_token = os.getenv("ACCESS_TOKEN")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        webex_payload = {
            "title": meeting_details["title"],
            "start": meeting_details["start"],
            "end": meeting_details["end"],
            "siteUrl": "cisco.webex.com",  # Ensures meetings are scheduled on the Cisco domain
            "invitees": [{"email": email} for email in meeting_details["invitees"]] + [{"email": "arsachde@cisco.com"}]
        }
        
        # Send the request to the Webex Meetings API
        response = requests.post(
            "https://webexapis.com/v1/meetings",
            headers=headers,
            json=webex_payload
        )
        print(f"Webex API response status code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            return {"message": "Meeting successfully booked!", "details": response.json()}
        else:
            return {"error": "Failed to book meeting", "details": response.json()}, response.status_code
    
    except Exception as e:
        return {"error": str(e)}, 500

def parse_meeting_request(natural_language_text):
    prompt = f"""
    You are a helpful assistant. Parse the following natural language text into JSON for a Webex meeting request:

    Input: "{natural_language_text}"
    JSON Format:
    {{
        "title": "Meeting Title",
        "start": "ISO 8601 Start Time (future-dated in UTC)",
        "end": "ISO 8601 End Time (future-dated in UTC, 1 hour after the start time if not explicitly mentioned)",
        "invitees": ["email1@example.com", "email2@example.com", "arsachde@cisco.com"]
    }}

    Today's date is {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')}. Ensure the start time is at least 30 minutes in the future. Assume a 1-hour duration if the end time is not explicitly mentioned. Always include 'arsachde@cisco.com' in the invitees list.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    
    parsed_json = response['choices'][0]['message']['content']
    try:
        return json.loads(parsed_json)  # Convert the string to a Python dictionary
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON from OpenAI response: {parsed_json}") from e
    return parsed_json

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)