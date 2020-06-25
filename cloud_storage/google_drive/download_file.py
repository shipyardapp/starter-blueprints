import os
import io
import re
import json
import tempfile
import argparse

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-file-name-match-type', dest='source_file_name_match_type',
                        choices={'exact_match', 'regex_match'}, required=True)
    parser.add_argument('--source-folder-name',
                        dest='source_folder_name', default='', required=False)
    parser.add_argument('--source-file-name',
                        dest='source_file_name', required=True)
    parser.add_argument('--destination-file-name',
                        dest='destination_file_name', default=None, required=False)
    parser.add_argument('--destination-folder-name',
                        dest='destination_folder_name', default='', required=False)
    parser.add_argument('--service-account', dest='gcp_application_credentials',
                        default=None, required=True)
    parser.add_argument('--drive', dest='drive', default=None, required=False)
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


def extract_file_name_from_source_full_path(source_full_path):
    """
    Use the file name provided in the source_file_name variable. Should be run only
    if a destination_file_name is not provided.
    """
    destination_file_name = os.path.basename(source_full_path)
    return destination_file_name


def enumerate_destination_file_name(destination_file_name, file_number=1):
    """
    Append a number to the end of the provided destination file name.
    Only used when multiple files are matched to, preventing the destination file from being continuously overwritten.
    """
    if re.search(r'\.', destination_file_name):
        destination_file_name = re.sub(
            r'\.', f'_{file_number}.', destination_file_name, 1)
    else:
        destination_file_name = f'{destination_file_name}_{file_number}'
    return destination_file_name


def determine_destination_file_name(*, source_full_path, destination_file_name, file_number=None):
    """
    Determine if the destination_file_name was provided, or should be extracted from the source_file_name, 
    or should be enumerated for multiple file downloads.
    """
    if destination_file_name:
        if file_number:
            destination_file_name = enumerate_destination_file_name(
                destination_file_name, file_number)
        else:
            destination_file_name = destination_file_name
    else:
        destination_file_name = extract_file_name_from_source_full_path(
            source_full_path)

    return destination_file_name


def clean_folder_name(folder_name):
    """
    Cleans folders name by removing duplicate '/' as well as leading and trailing '/' characters.
    """
    folder_name = folder_name.strip('/')
    if folder_name != '':
        folder_name = os.path.normpath(folder_name)
    return folder_name


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')
    combined_name = os.path.normpath(combined_name)

    return combined_name


def determine_destination_name(destination_folder_name, destination_file_name, source_full_path, file_number=None):
    """
    Determine the final destination name of the file being downloaded.
    """
    destination_file_name = determine_destination_file_name(
        destination_file_name=destination_file_name, source_full_path=source_full_path, file_number=file_number)
    destination_name = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)
    return destination_name


def find_folder_id(service, destination_folder_name, _all=False, drive_id=False):
    """
    Returns the id of the destination folder name in Google Drive
    """
    parent_id = None
    parent_ids = []
    folders = destination_folder_name.split('/')
    if not folders:
        folders = [destination_folder_name]
    for folder in folders:
        # build query string
        if parent_id:
            query = 'mimeType = \'application/vnd.google-apps.folder\'' \
                f' and name=\'{folder}\' and \'{parent_id}\' in parents'
        else:
            query = 'mimeType = \'application/vnd.google-apps.folder\''
            if folder != '':
                query += f' and name=\'{folder}\''

        if drive_id:
            results = service.files().list(q=str(query), supportsAllDrives=True,
                            includeItemsFromAllDrives=True, corpora="drive",
                            driveId=drive_id,
                            fields="files(id, name)").execute()
        else:
            results = service.files().list(q=str(query),
                    fields="files(id, name)").execute()

        _folder = results.get('files', [])
        if _folder != []:
            parent_id = _folder[0].get('id')
            parent_ids.append(parent_id)
        else:
            parent_id = None

    if _all:
        return parent_ids
    return parent_id


def get_all_folder_ids(service, parent_id=None, drive_id=False):
    """
    Returns the id of the destination folder name in Google Drive
    """
    parent_ids = []
    # build query string
    if parent_id:
        query = 'mimeType = \'application/vnd.google-apps.folder\'' \
            f' and \'{parent_id}\' in parents'
    else:
        query = 'mimeType = \'application/vnd.google-apps.folder\''

    try:
        if drive_id:
             results = service.files().list(q=str(query), supportsAllDrives=True,
                        includeItemsFromAllDrives=True, corpora="drive",
                        driveId=drive_id,
                        fields="files(id, name)").execute()
        else:
            results = service.files().list(q=str(query),
                    fields="files(id, name)").execute()
    except Exception as e:
        print(f'Failed to fetch folder ids for folder {parent_id}')
        raise(e)

    folders = results.get('files', [])
    return set(folder['id'] for folder in folders)



def find_google_drive_file_names(service, prefix='', drive=None):
    """
    Fetched all the files in the Drive which are returned in a list as 
    Google Blob objects
    """
    drive_id = None
    if drive:
        drive_id = get_shared_drive_id(service, drive)

    if prefix:
        parent_folder_id = find_folder_id(service, prefix, drive_id=drive_id)
        parent_folder_ids = get_all_folder_ids(service,
                                parent_id=parent_folder_id, drive_id=drive_id)
        parent_folder_ids.add(parent_folder_id)
        parent_folder_ids.add(drive_id)
    else:
        parent_folder_ids = get_all_folder_ids(service, drive_id=drive_id)
        parent_folder_ids.add(drive_id)

    files = []
    parent_folder_ids = list(filter(None, parent_folder_ids))
    for parent_folder_id in parent_folder_ids:
        query = f'\'{parent_folder_id}\' in parents'
        if drive:
            _files = service.files().list(q=str(query), supportsAllDrives=True,
                    includeItemsFromAllDrives=True, corpora="drive",
                    driveId=drive_id,
                    fields="files(id, name)").execute()
        else:
            _files = service.files().list(q=str(query),
                                    fields="files(id, name)").execute()
        files.extend(_files.get('files', []))
    return files


def find_matching_files(file_blobs, file_name_re):
    """
    Return a list of all file_names that matched the regular expression.
    """
    matching_file_names = []
    for blob in file_blobs:
        if re.search(file_name_re, blob['name']):
            matching_file_names.append(blob)

    return matching_file_names


def download_google_drive_file(service, blob, destination_file_name=None):
    """
    Download a selected file from Google Drive to local storage in
    the current working directory.
    """
    local_path = os.path.normpath(f'{os.getcwd()}/{destination_file_name}')
    name = blob['name']
    path = local_path.rsplit('/', 1)[0]
    if not os.path.exists(path):
        os.mkdir(path)
    fh = io.FileIO(local_path, 'wb+')
    try:
        request = service.files().get_media(fileId=blob['id'])
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
    except Exception as e:
        print(f'{name} failed to downoad')
        raise(e)

    print(f'{name} successfully downloaded to {local_path}')

    return


def get_shared_drive_id(service, drive):
    """
    Search for the drive under shared Google Drives.
    """
    drives = service.drives().list().execute()
    drive_id = None
    for _drive in drives['drives']:
        if _drive['name'] == drive:
            drive_id = _drive['id']
    return drive_id


def get_file_blob(service, source_folder_name, source_file_name, drive):
    """
    Return a single file blob that matched the source file name.
    """
    query = f'name contains \'{source_file_name}\' '

    if drive:
        drive_id = get_shared_drive_id(service, drive)
        if source_folder_name != '':
            parent_folder_id = find_folder_id(service, source_folder_name,
                                                drive_id=drive_id)
            query += f'and \'{parent_folder_id}\' in parents'
        files = service.files().list(q=str(query), supportsAllDrives=True,
                includeItemsFromAllDrives=True, corpora="drive",
                driveId=drive_id,
                fields="files(id, name)").execute()
    else:
        if source_folder_name != '':
            parent_folder_id = find_folder_id(service, source_folder_name)
            query += f'and \'{parent_folder_id}\' in parents'
        files = service.files().list(q=str(query),
                fields="files(id, name)").execute()
    files = files.get('files', [])
    return files[0] if files != [] else None



def get_service(credentials):
    """
    Attempts to create the Google Drive Client with the associated
    environment variables
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f'Error accessing Google Drive with service account ' \
                f'{credentials}')
        raise(e)


def main():
    args = get_args()
    tmp_file = set_environment_variables(args)
    drive = args.drive
    source_file_name = args.source_file_name
    source_folder_name = clean_folder_name(args.source_folder_name)
    source_full_path = combine_folder_and_file_name(
        folder_name=source_folder_name, file_name=source_file_name)
    source_file_name_match_type = args.source_file_name_match_type

    destination_folder_name = clean_folder_name(args.destination_folder_name)
    if not os.path.exists(destination_folder_name) and \
            (destination_folder_name != ''):
        os.makedirs(destination_folder_name)

    if tmp_file:
        service = get_service(credentials=tmp_file)
    else:
        service = get_service(credentials=args.gcp_application_credentials)

    if source_file_name_match_type == 'regex_match':
        files = find_google_drive_file_names(service=service, drive=drive,
                                            prefix=source_folder_name)
        matching_file_names = find_matching_files(files,
                                            re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to download...')

        for index, blob in enumerate(matching_file_names):
            destination_name = determine_destination_name(
                    destination_folder_name=destination_folder_name,
                    destination_file_name=args.destination_file_name,
                    source_full_path=blob['name'], file_number=index+1)

            print(f'Downloading file {index+1} of {len(matching_file_names)}')
            try:
                download_google_drive_file(service=service, blob=blob,
                    destination_file_name=destination_name)
            except Exception as e:
                print(f'Failed to download {blob["name"]}... Skipping')
    else:
        blob = get_file_blob(service=service, drive=drive,
                            source_folder_name=source_folder_name,
                                source_file_name=source_file_name)
        if not blob:
            print(f'Could not find file {source_file_name} in folder ' \
                    f'{source_folder_name}')
            return
        destination_name = determine_destination_name(
                destination_folder_name=destination_folder_name,
                destination_file_name=args.destination_file_name,
                source_full_path=source_full_path)

        download_google_drive_file(service=service, blob=blob,
                destination_file_name=destination_name)
    if tmp_file:
        print(f'Removing temporary credentials file {tmp_file}')
        os.remove(tmp_file)


if __name__ == '__main__':
    main()
