from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import datetime
import os
import pickle
from google.auth.transport.requests import Request

# Authenticate and create a service instance
def authenticate_google_calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    # Check if token.pickle exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds)

# Create an event on Google Calendar
def create_google_calendar_event(service):
    webex_meeting_details = """
Meeting link: https://cisco.webex.com/meet/arsachde
Meeting number: 1869 41 0779

Join from a video conferencing system or application:
Dial: arsachde@cisco.webex.com

Join by phone:
Call-in toll number (US/Canada): +1-408-525-6800
Access code: 1869 41 0779
    """

    event = {
        'summary': 'Webex Meeting',
        'description': 'This is a Webex meeting. Details below:\n\n' + webex_meeting_details,
        'start': {
            'dateTime': '2025-01-26T19:00:00+00:00',  # 3 PM UK Time in UTC
            'timeZone': 'Europe/London',
        },
        'end': {
            'dateTime': '2025-01-26T20:00:00+00:00',  # 4 PM UK Time in UTC
            'timeZone': 'Europe/London',
        },
        'attendees': [
            {'email': 'arsachde@cisco.com'},
            {'email': 'archit.sachdeva007@gmail.com'}
        ],
        'location': 'https://cisco.webex.com/meet/arsachde',
    }

    event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
    print('Event created: %s' % (event.get('htmlLink')))

if __name__ == '__main__':
    service = authenticate_google_calendar()
    create_google_calendar_event(service)