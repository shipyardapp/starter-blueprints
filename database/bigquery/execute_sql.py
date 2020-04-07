import fileinput
from google.cloud import bigquery


def create_creds_json():
    json_format = eval(os.getenv("GOOGLE_CREDS_JSON"))

    with open('creds.json', 'w') as out_file:
        json.dump(json_format, out_file)

    with fileinput.FileInput('creds.json', inplace=True, backup='.bak') as file:
        for line in file:
            print(line.replace('\\\\n', '\\n'), end='')


def get_credentials():
    create_service_account()
    # SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive',
    #           'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.appdata',
    #           'https://www.googleapis.com/auth/drive.apps.readonly']

    credentials = service_account.Credentials.from_service_account_file('creds.json)

    return credentials


create_creds_json()
