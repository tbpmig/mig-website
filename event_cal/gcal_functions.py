#Google Calendar Test
#-- if errors on running, need to add proper prefix to imports
from gcal import gflags
from gcal import httplib2

from gcal.apiclient.discovery import build
from gcal.oauth2client.file import Storage
from gcal.oauth2client.client import OAuth2WebServerFlow
from gcal.oauth2client.tools import run

from django.shortcuts import redirect

import migweb.local_settings

FLAGS = gflags.FLAGS
FLAGS.auth_local_webserver = False

# Set up a Flow object to be used if we need to authenticate. This
# sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
# the information it needs to authenticate. Note that it is called
# the Web Server Flow, but it can also handle the flow for native
# applications
# The client_id and client_secret are copied from the API Access tab on
# the Google APIs Console
CALENDAR_DATA = migweb.local_settings.gcal_cal_data
FLOW = OAuth2WebServerFlow(
    client_id=migweb.local_settings.gcal_client_id,
    client_secret=migweb.local_settings.gcal_client_secret,
    scope='https://www.googleapis.com/auth/calendar',
    user_agent='migweb/0',
    redirect_uri=migweb.local_settings.gcal_redirect_uri,
    approval_prompt='force',
    access_type='offline')

def initialize_gcal():
    auth_uri = FLOW.step1_get_authorize_url()
    return redirect(auth_uri)
def get_credentials():
    # To disable the local server feature, uncomment the following line:

    # If the Credentials don't exist or are invalid, run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage(CALENDAR_DATA)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run(FLOW,storage)
    return credentials
def process_auth(code):
    credentials=FLOW.step2_exchange(code)
    storage = Storage(CALENDAR_DATA)
    storage.put(credentials)
    return credentials
def get_authorized_http(credentials):
    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    if credentials is None or credentials.invalid == True:
        return None
    http = httplib2.Http()
    return credentials.authorize(http)

def get_service(http):
    if http:
        return build(serviceName='calendar', version='v3',http=http,
                     developerKey=migweb.local_settings.gcal_developerKey)

#Event Format
event = {
    'summary': 'Test',
    'location': 'Somewhere',
    'start': {
        'dateTime': '2013-10-08T10:00:00.000-07:00',
        'timeZone': 'America/Detroit'
    },
    'end': {
        'dateTime': '2013-10-08T10:25:00.000-07:00',
        'timeZone': 'America/Detroit'
    },
#  'recurrence': [
#   # 'RRULE:FREQ=WEEKLY;UNTIL=20110701T100000-07:00',
#  ],
#  'attendees': [
#   # {
#   #   'email': 'attendeeEmail',
#      # Other attendee's data...
#   # },
#    # ...
#  ],
}
#print event
#Set calendarId appropriately
#recurring_event = service.events().insert(calendarId='7sh4sos0nfm3av7cqelg6n9m1o@group.calendar.google.com', body=event).execute()
#
#print recurring_event['id']
