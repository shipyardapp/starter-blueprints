import os
import re
import json
import csv
import tempfile
import argparse
import glob

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SCOPES = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']
#SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-file-name', dest='source_file_name',
            required=True)
    parser.add_argument('--source-folder-name', dest='source_folder_name',
            default='', required=False)
    parser.add_argument('--sheet-name',
            dest='sheet_name', default='', required=False)
    parser.add_argument('--starting-cell',
            dest='starting_cell', default='A1', required=False)
    parser.add_argument('--workbook-name', dest='workbook_name',
            default=None, required=False)
    parser.add_argument('--service-account', dest='gcp_application_credentials',
            default=None, required=True)
    return parser.parse_args()


def set_environment_variables(args):
    """
    Set GCP credentials as environment variables if they're provided via keyword
    arguments rather than seeded as environment variables. This will override
    system defaults.
    """
    credentials = args.gcp_application_credentials
    try:
        json_credentials = json.loads(credentials)
        fd, path = tempfile.mkstemp()
        print(f'Storing json credentials temporarily at {path}')
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(credentials)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
        return path
    except Exception:
        print('Using specified json credentials file')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials
        return


def clean_folder_name(folder_name):
    """
    Cleans folders name by removing duplicate '/' as well as leading and
    trailing '/' characters.
    """
    folder_name = folder_name.strip('/')
    if folder_name != '':
        folder_name = os.path.normpath(folder_name)
    return folder_name


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path
    variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')
    combined_name = os.path.normpath(combined_name)

    return combined_name


def check_workbook_exists(service, spreadsheet_id, workbook_name):
    """
    Checks if the workbook exists within the spreadsheet.
    """
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet['sheets']
        exists = [True for sheet in sheets if sheet['properties']['title'] == workbook_name]
        return True if exists else False
    except Exception as e:
        print(f'Failed to check workbook {workbook_name} for spreadsheet ' \
                f'{spreadsheet_id}')
        raise(e)


def add_workbook(service, spreadsheet_id, workbook_name):
    """
    Adds a workbook to the spreadsheet.
    """
    try:
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': workbook_name,
                    }
                }
            }]
        }

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        ).execute()

        return response
    except Exception as e:
        print(e)


def upload_google_sheets_file(
        service,
        sheet_name,
        source_full_path,
        starting_cell,
        spreadsheet_id,
        workbook_name):
    """
    Uploads a single file to Google Sheets.
    """
    try:
        if not spreadsheet_id:
            file_metadata = {'properties': {'title': sheet_name}}
            spreadsheet = service.spreadsheets().create(body=file_metadata,
                                                fields='spreadsheetId').execute()
            spreadsheet_id = spreadsheet['spreadsheetId']

        # check if the workbook exists and create it if it doesn't
        workbook_exists = check_workbook_exists(service=service,
                                              spreadsheet_id=spreadsheet_id,
                                              workbook_name=workbook_name)
        if not workbook_exists:
            add_workbook(service=service, spreadsheet_id=spreadsheet_id,
                            workbook_name=workbook_name)

        data = []
        with open(source_full_path, newline='') as f:
            reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)
            for row in reader:
                # stripping any empty rows
                if set(row) != {''}:
                    data.append(row)

        if starting_cell:
            _range = f'{starting_cell}:ZZZ5000000'
        else:
            _range = 'A1:ZZZ5000000'

        if workbook_name:
            _range = f'{workbook_name}!{_range}'

        body = {'value_input_option': 'RAW',
                'data': [{
                    'values': data,
                    'range': _range,
                    'majorDimension': 'ROWS'}]
                }
        response = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id,
                body=body).execute()
    except Exception as e:
        if isinstance(e, FileNotFoundError):
            print(f'File {source_full_path} does not exist.')
        elif hasattr(e, 'content'):
            err_msg = json.loads(e.content)
            if 'workbook above the limit' in err_msg['error']['message']:
                print(f'Failed to upload due to input csv size {source_full_path}' \
                        ' being to large (Limit is 5,000,000 cells)')
        else:
            print(f'Failed to upload spreadsheet {source_full_path} to ' \
                    f'{sheet_name}')
        raise(e)

    print(f'{source_full_path} successfully uploaded to {sheet_name}')


def get_spreadsheet_id_by_name(drive_service, sheet_name):
    """
    Attempts to get sheet id from the Google Drive Client using the
    sheet name
    """
    try:
        query = 'mimeType="application/vnd.google-apps.spreadsheet"'
        query += f' and name = "{sheet_name}"'
        results = drive_service.files().list(q=str(query)).execute()
        files = results['files']
        for _file in files:
            return _file['id']
        return None
    except Exception as e:
        print(f'Failed to fetch spreadsheetId for {sheet_name}')
        raise(e)


def get_service(credentials):
    """
    Attempts to create the Google Drive Client with the associated
    environment variables
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        return service, drive_service
    except Exception as e:
        print(f'Error accessing Google Drive with service account ' \
                f'{credentials}')
        raise(e)


def main():
    args = get_args()
    tmp_file = set_environment_variables(args)
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    source_full_path = combine_folder_and_file_name(
        folder_name=f'{os.getcwd()}/{source_folder_name}',
        file_name=source_file_name)
    sheet_name = clean_folder_name(args.sheet_name)
    workbook_name = args.workbook_name
    starting_cell = args.starting_cell

    if tmp_file:
        service, drive_service = get_service(credentials=tmp_file)
    else:
        service, drive_service = get_service(credentials=args.gcp_application_credentials)

    spreadsheet_id = get_spreadsheet_id_by_name(drive_service=drive_service,
                                            sheet_name=sheet_name)
    # check if workbook exists in the spreadsheet
    upload_google_sheets_file(service=service, sheet_name=sheet_name,
                              source_full_path=source_full_path,
                              spreadsheet_id=spreadsheet_id,
                              workbook_name=workbook_name,
                              starting_cell=starting_cell)

    if tmp_file:
        print(f'Removing temporary credentials file {tmp_file}')
        os.remove(tmp_file)


if __name__ == '__main__':
    main()
