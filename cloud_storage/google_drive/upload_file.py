import os
import re
import json
import tempfile
import argparse
import glob

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-file-name-match-type',
            dest='source_file_name_match_type',
            choices={
                'exact_match',
                'regex_match'},
            required=True)
    parser.add_argument('--source-file-name', dest='source_file_name',
            required=True)
    parser.add_argument('--source-folder-name', dest='source_folder_name',
            default='', required=False)
    parser.add_argument('--destination-folder-name',
            dest='destination_folder_name', default='', required=False)
    parser.add_argument('--destination-file-name', dest='destination_file_name',
            default=None, required=False)
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
    Use the file name provided in the source_full_path variable. Should be run
    only if a destination_file_name is not provided.
    """
    destination_file_name = os.path.basename(source_full_path)
    return destination_file_name


def enumerate_destination_file_name(destination_file_name, file_number=1):
    """
    Append a number to the end of the provided destination file name.
    Only used when multiple files are matched to, preventing the destination
    file from being continuously overwritten.
    """
    if re.search(r'\.', destination_file_name):
        destination_file_name = re.sub(
            r'\.', f'_{file_number}.', destination_file_name, 1)
    else:
        destination_file_name = f'{destination_file_name}_{file_number}'
    return destination_file_name


def determine_destination_file_name(
    *,
    source_full_path,
    destination_file_name,
        file_number=None):
    """
    Determine if the destination_file_name was provided, or should be extracted
    from the source_file_name, or should be enumerated for multiple file
    uploads.
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


def determine_destination_full_path(
        destination_folder_name,
        destination_file_name,
        source_full_path,
        file_number=None):
    """
    Determine the final destination name of the file being uploaded.
    """
    destination_file_name = determine_destination_file_name(
        destination_file_name=destination_file_name,
        source_full_path=source_full_path,
        file_number=file_number)
    destination_full_path = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)
    return destination_full_path


def find_all_local_file_names(source_folder_name):
    """
    Returns a list of all files that exist in the current working directory,
    filtered by source_folder_name if provided.
    """
    cwd = os.getcwd()
    cwd_extension = os.path.normpath(f'{cwd}/{source_folder_name}/**')
    file_names = glob.glob(cwd_extension, recursive=True)
    return [file_name for file_name in file_names if os.path.isfile(file_name)]


def find_all_file_matches(file_names, file_name_re):
    """
    Return a list of all file_names that matched the regular expression.
    """
    matching_file_names = []
    for file in file_names:
        if re.search(file_name_re, file):
            matching_file_names.append(file)

    return matching_file_names


def create_remote_folder(service, folder, parent_id=None, drive_id=None):
    """
    Create a folder on Drive, returns the newely created folders ID
    """
    body = {
      'name': folder,
      'mimeType': "application/vnd.google-apps.folder"
    }
    if parent_id:
        body['parents'] = [parent_id]
    if drive_id and not parent_id:
        body['parents'] = [drive_id]
    try:
        folder = service.files().create(body=body, supportsAllDrives=True,
                                       fields=('id')).execute()
        print(f'Creating folder: {folder}')
    except Exception as e:
        print(f'Failed to create folder: {folder}')
        raise(e)
    return folder['id']


def find_folder_id(service, destination_folder_name, drive):
    """
    Returns the id of the destination folder name in Google Drive
    """
    parent_id = None
    for folder in destination_folder_name.split('/')[:-1]:
        # build query string
        if parent_id:
            query = 'mimeType = \'application/vnd.google-apps.folder\'' \
                f' and name=\'{folder}\' and \'{parent_id}\' in parents'
        else:
            query = 'mimeType = \'application/vnd.google-apps.folder\'' \
                f' and name=\'{folder}\''

        if drive:
            drive_id = get_shared_drive_id(service, drive)
            results = service.files().list(q=str(query), supportsAllDrives=True,
                            includeItemsFromAllDrives=True, corpora="drive",
                            driveId=drive_id,
                            fields="files(id, name)").execute()
        else:
            drive_id = None
            results = service.files().list(q=str(query),
                    fields="files(id, name)").execute()

        _folder = results.get('files', [])
        if _folder != []:
            parent_id = _folder[0].get('id')
        else:
            parent_id = create_remote_folder(service, folder, parent_id,
                                            drive_id)

    return parent_id


def upload_google_drive_file(
        service,
        source_full_path,
        destination_full_path,
        parent_folder_id,
        drive):
    """
    Uploads a single file to Google Drive.
    """
    file_metadata = {'name': destination_full_path}
    file_name = destination_full_path.rsplit('/', 1)[-1]
    if file_name:
        file_metadata = {'name': file_name,
                         'parents': []}

    drive_id = None
    if drive:
        drive_id = get_shared_drive_id(service, drive)

    if parent_folder_id:
        file_metadata['parents'].append(parent_folder_id)
    elif drive_id:
        parent_folder_id = drive_id
        file_metadata['parents'].append(drive_id)
    else:
        parent_folder_id = 'root'

    # Check if file exists
    update = False
    if drive_id:
        query = f'name=\'{file_name}\' and \'{parent_folder_id}\' in parents'
        exists = service.files().list(q=query,
                            includeItemsFromAllDrives=True, corpora="drive",
                            driveId=drive_id, supportsAllDrives=True).execute()
    else:
        query = f'name=\'{file_name}\' and \'{parent_folder_id}\' in parents'
        exists = service.files().list(q=query).execute()

    if exists.get('files', []) != []:
        file_id = exists['files'][0]['id']
        update = True
        parent_folder_id = file_metadata.pop('parents')[0]

    try:
        media = MediaFileUpload(source_full_path, resumable=True)
    except Exception as e:
        print(f'The file {source_full_path} does not exist')
        raise(e)

    try:
        if update:
            _file = service.files().update(fileId=file_id, body=file_metadata,
                                media_body=media, supportsAllDrives=True,
                                fields=('id'), addParents=parent_folder_id).execute()
        else:
            _file = service.files().create(body=file_metadata,
                                media_body=media, supportsAllDrives=True,
                                fields=('id')).execute()
    except Exception as e:
        if e.content == b'Failed to parse Content-Range header.':
            print(f'Failed to upload file {source_full_path} due to invalid size')
        print(f'Failed to upload file: {file_name}')
        raise (e)

    print(f'{source_full_path} successfully uploaded to ' \
            f'{destination_full_path}')


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
    source_folder_name = args.source_folder_name
    source_full_path = combine_folder_and_file_name(
        folder_name=f'{os.getcwd()}/{source_folder_name}',
        file_name=source_file_name)
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    source_file_name_match_type = args.source_file_name_match_type

    if tmp_file:
        service = get_service(credentials=tmp_file)
    else:
        service = get_service(credentials=args.gcp_application_credentials)

    if source_file_name_match_type == 'regex_match':
        file_names = find_all_local_file_names(source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to upload...')

        for index, key_name in enumerate(matching_file_names):
            destination_full_path = determine_destination_full_path(
                            destination_folder_name=destination_folder_name,
                            destination_file_name=args.destination_file_name,
                            source_full_path=key_name, file_number=index + 1)

            # if destination folder is specified, confirm the folder exists
            parent_folder_id = None
            if destination_folder_name:
                parent_folder_id = find_folder_id(service, destination_full_path,
                                                    drive)
                if not parent_folder_id:
                    print(f'Folder {destination_folder_name} does not exist')
                    return

            print(f'Uploading file {index+1} of {len(matching_file_names)}')
            upload_google_drive_file(source_full_path=key_name, drive=drive,
                            destination_full_path=destination_full_path,
                            service=service, parent_folder_id=parent_folder_id)

    else:
        destination_full_path = determine_destination_full_path(
                            destination_folder_name=destination_folder_name,
                            destination_file_name=args.destination_file_name,
                            source_full_path=source_full_path)
        # if destination folder is specified, confirm the folder exists
        parent_folder_id = None
        if destination_folder_name:
            parent_folder_id = find_folder_id(service, destination_full_path,
                                                drive)
            if not parent_folder_id:
                print(f'Folder {destination_folder_name} does not exist')
                return

        upload_google_drive_file(source_full_path=source_full_path, drive=drive,
                    destination_full_path=destination_full_path,
                    service=service, parent_folder_id=parent_folder_id)
    if tmp_file:
        print(f'Removing temporary credentials file {tmp_file}')
        os.remove(tmp_file)


if __name__ == '__main__':
    main()
