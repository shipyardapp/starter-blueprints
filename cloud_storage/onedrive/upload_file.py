import os
import re

import json
import tempfile
import argparse
import glob

import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer

REDIRECT_URL = 'http://localhost:8080/'
API_BASE_URL='https://api.onedrive.com/v1.0/'
SCOPES=['wl.signin', 'wl.offline_access', 'onedrive.readwrite']


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
    parser.add_argument('--client-id', dest='client_id',
            default=None, required=True)
    parser.add_argument('--client-secret', dest='client_secret',
            default=None, required=True)
    return parser.parse_args()


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
    return file_names


def find_all_file_matches(file_names, file_name_re):
    """
    Return a list of all file_names that matched the regular expression.
    """
    matching_file_names = []
    for file in file_names:
        if re.search(file_name_re, file):
            matching_file_names.append(file)

    return matching_file_names


def upload_onedrive_file(
        client,
        source_full_path,
        destination_full_path):
    """
    Uploads a single file to OneDrive.
    """
    destination_path, destination_name = destination_full_path.rsplit('/', 1) 
    folder = client.item(drive='me', path=destination_path)
    item = folder.children[destination_name].upload_async(source_full_path)

    print(f'{source_full_path} successfully uploaded to {destination_full_path}')


def get_client(client_id, client_secret):
    """
    Attempts to create the One Drivfe Client with the associated
    client credentials
    """
    try:
        http_provider = onedrivesdk.HttpProvider()
        auth_provider = onedrivesdk.AuthProvider(
            http_provider=http_provider,
            client_id=client_id,
            scopes=SCOPES)

        client = onedrivesdk.OneDriveClient(API_BASE_URL, auth_provider,
                                            http_provider)
        auth_url = client.auth_provider.get_auth_url(REDIRECT_URL)
        code = GetAuthCodeServer.get_auth_code(auth_url, REDIRECT_URL)
        client.auth_provider.authenticate(code, REDIRECT_URL, client_secret)
        return client
    except Exception as e:
        print(f'Error accessing OneDrive with the specified credentials ' \
                f'{client_id}:{client_secret}')
        raise(e)


def main():
    args = get_args()
    client_id = args.client_id
    client_secret = args.client_secret
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    source_full_path = combine_folder_and_file_name(
        folder_name=f'{os.getcwd()}/{source_folder_name}',
        file_name=source_file_name)
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    source_file_name_match_type = args.source_file_name_match_type

    client = get_client(client_id=client_id, client_secret=client_secret)

    if source_file_name_match_type == 'regex_match':
        file_names = find_all_local_file_names(source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to upload...')

        for index, key_name in enumerate(matching_file_names):
            destination_full_path = determine_destination_full_path(
                destination_folder_name=destination_folder_name,
                destination_file_name=args.destination_file_name,
                source_full_path=key_name,
                file_number=index + 1)
            print(f'Uploading file {index+1} of {len(matching_file_names)}')
            upload_onedrive_file(
                source_full_path=key_name,
                destination_full_path=destination_full_path,
                client=client)

    else:
        destination_full_path = determine_destination_full_path(
            destination_folder_name=destination_folder_name,
            destination_file_name=args.destination_file_name,
            source_full_path=source_full_path)
        upload_onedrive_file(
            source_full_path=source_full_path,
            destination_full_path=destination_full_path,
            client=client)


if __name__ == '__main__':
    main()
