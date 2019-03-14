import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import re
import subprocess as sp
from datetime import datetime
from multiprocessing import Pool
from functools import partial
import time

def get_auth():
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

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
        return
    # ping_status = sp.call(['ping', target_ip], stdout=sp.DEVNULL)
    ping_status = sp.call(['ping', '-c', '5', '-q', target_ip], stdout=sp.DEVNULL)

    return ping_status

def update_sheet_status(sheet, sheet_id, range_, text):
    values = [ [ text ] ]
    body = { 'values': values }
    result = sheet.values().update(
                spreadsheetId=sheet_id, range=range_,
                valueInputOption='USER_ENTERED', body=body).execute()
    return result

def update_server_sheet(range_numb, sheet, sheet_id, sheet_name):
    target_ip_range = sheet_name+'!'+'F'+str(range_numb)
    target_ip = get_value_from_sheet(sheet, sheet_id, target_ip_range)
    ping_status = ping_server(target_ip)
    if ping_status == None:
        return

    target_status_range = sheet_name+'!'+'G'+str(range_numb)
    if ping_status == 0:
        update_sheet_status(sheet, sheet_id, 
                            target_status_range, 'ON')
    else:
        update_sheet_status(sheet, sheet_id, 
                            target_status_range, 'OFF')

    modified_time_range = sheet_name+'!'+'H'+str(range_numb)
    update_sheet_status(sheet, sheet_id, 
                        modified_time_range, str(datetime.now()))

def single_update_server_sheet(sheet_id, sheet_name, start_range, end_range):
    creds = get_auth()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    for range_numb in range(start_range, end_range+1):
        update_server_sheet(range_numb, sheet, sheet_id, sheet_name)

def multi_update_server_sheet(sheet_id, sheet_name, start_range, end_range):
    creds = get_auth()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    with Pool(processes=4) as pool:
        f_update_server_sheet = partial(update_server_sheet, 
                                            sheet=sheet, 
                                            sheet_id=sheet_id, 
                                            sheet_name=sheet_name)
        pool.map(f_update_server_sheet, list(range(start_range, end_range+1)))

if __name__ == '__main__':
    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = '1q4JKDHPubUlub8XbGVShh9ZTCfkOyZnlX0Vlb41j2xM'
    SHEET_NAME = 'Sheet1'
    START_RANGE = 2
    END_RANGE = 57

    while True:
        print(str(datetime.now()))
        print('Server check start!')
        print()

        multi_update_server_sheet(SPREADSHEET_ID, SHEET_NAME, START_RANGE, END_RANGE)

        print(str(datetime.now()))
        print('Server check end.')
        print()

        time.sleep(100)
