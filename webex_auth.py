from flask import Flask, request, redirect
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Retrieve values from .env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN_URL = os.getenv("TOKEN_URL")
AUTH_URL = os.getenv("AUTH_URL")
SCOPES = os.getenv("SCOPES")

app = Flask(__name__)

@app.route("/")
def home():
    return f"<a href='https://webexapis.com/v1/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=spark:all spark:kms meeting:schedules_read meeting:participants_read meeting:preferences_write meeting:preferences_read meeting:participants_write meeting:schedules_write&state=set_state_here'>Click here to authenticate with Webex</a>"


@app.route("/callback")
def callback():
    # Get the authorization code from the query parameters
    code = request.args.get("code")
    if not code:
        return "Authorization failed or denied."

    # Exchange the authorization code for an access token
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

@app.route("/send_message")
def send_message():
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with the actual access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "roomId": "YOUR_ROOM_ID_HERE",  # Replace with the Webex room ID
        "text": "Hello from Donna V2!",
    }
    response = requests.post("https://webexapis.com/v1/messages", headers=headers, json=data)
    return f"Message sent! Response: {response.json()}"

if __name__ == "__main__":
    app.run(port=5000)