from flask import Flask, request, redirect
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)

CLIENT_ID = "C182502a5660222223fc09cc60c1a46ccd747b5ff5eb78e357b4b16abdb2d4621"
CLIENT_SECRET = "e8e166f33a9c0b4987bb3e724ff7f6d7a23891ae8cdf0d8324a10d02556c7bc9"
REDIRECT_URI = "https://jennet-amazing-sailfish.ngrok-free.app"
TOKEN_URL = "https://webexapis.com/v1/access_token"


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


if __name__ == "__main__":
    app.run(port=5000)