from flask import Flask, render_template, request, redirect, url_for, session, request
import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
app.secret_key = 'lockin2024DavisHansonEnochAaronDarius'  # Set a secret key for session management

SCOPES = ["https://www.googleapis.com/auth/calendar"]
credentials_json = {
    "installed": {
        "client_id": "<your-client-id>",
        "project_id": "<your-project-id>",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "<your-client-secret>",
        "redirect_uris": ["http://localhost:5000/callback"]
    }
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        subjects = request.form.get('subjects')
        # Redirect and pass subjects as a query parameter
        return redirect(url_for('schedule', subjects=subjects))
    return render_template('index.html')

@app.route('/schedule')
def schedule():
    subjects = request.args.get('subjects', default="")
    subjects_list = subjects.split(',') if subjects else []
    return render_template('schedule.html', subjects=subjects_list)

@app.route('/add_study_time', methods=['POST'])
def add_study_time():
    subject = request.args.get('subject', '')
    response = request.form.get('response', 'no')
    if response == 'yes':
        # Assuming start_time and end_time are calculated or retrieved from somewhere
        start_time = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
        end_time = start_time + dt.timedelta(hours=1)  # Example end time
        success, message = add_calendar_event(f"Study Time - {subject}", start_time, end_time)
        if success:
            return render_template('confirmation.html', message=f"Study time added successfully! Event link: {message}")
        else:
            return render_template('confirmation.html', message=f"Failed to add study time: {message}")
    else:
        return render_template('confirmation.html', message="No study time added.")

@app.route('/list_events')
def list_events():
    # Assure that session credentials are loaded correctly
    credentials = Credentials(**session.get('credentials', {}))

    service = build('calendar', 'v3', credentials=credentials)
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return 'No upcoming events found.'
    return render_template('schedule.html', events=events)

@app.route('/callback')
def callback():
    state = request.args.get('state', None)
    code = request.args.get('code', None)
    
    if not state or not code:
        return 'Missing state or code in request', 400

    # Assuming 'state' matches what you expect
    flow = InstalledAppFlow.from_client_config(credentials_json, SCOPES, state=state)
    flow.fetch_token(code=code)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    
    return redirect(url_for('index'))

def add_calendar_event(summary, start_time, end_time):
    try:
        creds = None
        if 'credentials' in session:
            creds = Credentials(**session['credentials'])

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(credentials_json, SCOPES)
                creds = flow.run_local_server(port=0)
                session['credentials'] = credentials_to_dict(creds)

        service = build("calendar", "v3", credentials=creds)

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'colorId': '11'
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return True, created_event.get('htmlLink')
    except HttpError as error:
        print("An error occurred: %s" % error)
        return False, "Google API error"
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return False, "Unexpected error"

if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)
