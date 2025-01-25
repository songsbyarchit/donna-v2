from flask import Flask, request, redirect
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=".env", override=True)

# Retrieve values from .env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN_URL = os.getenv("TOKEN_URL")
AUTH_URL = os.getenv("AUTH_URL")
SCOPES = os.getenv("SCOPES")
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)