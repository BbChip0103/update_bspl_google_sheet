from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import re
import subprocess as sp
from datetime import datetime

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1MWWlLMBB_GY9l-NTpQLeflBOzblsdQsF2zaLgDjEInc'
SHEET_NAME = 'Sheet1'
TARGET_RANGE = (2, 57)

def get_auth():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_value_from_sheet(sheet, sheet_id, range_):
    # Call the Sheets API
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_).execute()
    value = result.get('values', [])
    return value[0][0] if value else None

def ping_server(target_ip):
    if not target_ip or not re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', target_ip):
        print('unvalid IP address')
        return
    print(target_ip)
    ping_status = sp.call(['ping', target_ip])
    print(ping_status)
    return ping_status

def update_sheet_status(sheet, sheet_id, range_, text):
    values = [ [ text ] ]
    body = { 'values': values }
    result = sheet.values().update(
                spreadsheetId=sheet_id, range=range_,
                valueInputOption='USER_ENTERED', body=body).execute()
    return result

def main():
    creds = get_auth()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    for range_numb in range(*TARGET_RANGE):
        target_ip_range = SHEET_NAME+'!'+'F'+str(range_numb)
        target_ip = get_value_from_sheet(sheet, SPREADSHEET_ID, target_ip_range)
        ping_status = ping_server(target_ip)
        if ping_status == None:
            # return
            continue

        target_status_range = SHEET_NAME+'!'+'G'+str(range_numb)
        if ping_status == 0:
            update_sheet_status(sheet, SPREADSHEET_ID, 
                                target_status_range, 'Online')
        else:
            update_sheet_status(sheet, SPREADSHEET_ID, 
                                target_status_range, 'Offline')

        modified_time_range = SHEET_NAME+'!'+'H'+str(range_numb)
        update_sheet_status(sheet, SPREADSHEET_ID, 
                            modified_time_range, str(datetime.now()))

if __name__ == '__main__':
    main()