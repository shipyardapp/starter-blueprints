import os
import re
import json
import tempfile
import argparse
import glob

from boxsdk import OAuth2, Client
from boxsdk.exception import *

import logging
logging.getLogger('boxsdk').setLevel(logging.CRITICAL)



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
    parser.add_argument('--developer-token', dest='developer_token',
            default=None, required=True)
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


def upload_box_file(
        client,
        source_full_path,
        destination_full_path,
        folder_id):
    """
    Uploads a single file to Box.
    """
    destination_file_name = destination_full_path.rsplit('/', 1)[-1]
    with open(source_full_path, 'rb') as f:
        try:
            new_file = client.folder(folder_id).upload_stream(f,
                                                        destination_file_name)
        except Exception as e:
            print(f'Failed to upload file {source_full_path}')
            raise(e)

    print(f'{source_full_path} successfully uploaded to ' \
            f'{destination_full_path}')


def get_client(developer_token, client_id, client_secret):
    """
    Attempts to create the Box Client with the associated with the credentials.
    """
    try:
        auth = OAuth2(client_id=client_id, client_secret=client_secret,
                        access_token=developer_token)
        client = Client(auth)
        client.user().get()
        return client
    except BoxOAuthException as e:
        print(f'Error accessing Box account with pervice account ' \
              f'developer_token={developer_token}; client_id={client_id}; ' \
              f'client_secret={client_secret}')
        raise(e)

def get_folder_id(client, destination_folder_name):
    """
    Returns the folder id for the Box client if it exists.
    """
    try:
        folders = client.search().query(query=destination_folder_name,
                                            result_type='folder')
        for folder in folders:
            return folder.id
    except (BoxOAuthException, BoxAPIException) as e:
        print(f'The specified folder {destination_folder_name} does not exist')
        raise(e)


def main():
    args = get_args()
    developer_token = args.developer_token
    client_id = args.client_id
    client_secret = args.client_secret
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    source_full_path = combine_folder_and_file_name(
        folder_name=f'{os.getcwd()}/{source_folder_name}',
        file_name=source_file_name)
    destination_file_name = args.destination_file_name
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    source_file_name_match_type = args.source_file_name_match_type

    client = get_client(developer_token=developer_token, client_id=client_id,
                        client_secret=client_secret)
    folder_id = get_folder_id(client, destination_folder_name=destination_folder_name)

    if source_file_name_match_type == 'regex_match':
        file_names = find_all_local_file_names(source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to upload...')

        for index, file_name in enumerate(matching_file_names):
            destination_full_path = determine_destination_full_path(
                            destination_folder_name=destination_folder_name,
                            destination_file_name=args.destination_file_name,
                            source_full_path=file_name, file_number=index + 1)

            print(f'Uploading file {index+1} of {len(matching_file_names)}')
            upload_box_file(
                source_full_path=file_name,
                destination_full_path=destination_full_path,
                client=client, folder_id=folder_id)

    else:
        destination_full_path = determine_destination_full_path(
                            destination_folder_name=destination_folder_name,
                            destination_file_name=args.destination_file_name,
                            source_full_path=source_full_path)
        # if destination folder is specified, confirm the folder exists
        parent_folder_id = None
        if destination_folder_name:
            parent_folder_id = get_folder_id(client, destination_full_path)
            if not parent_folder_id:
                print(f'Folder {destination_folder_name} does not exist')
                return

        upload_box_file(source_full_path=source_full_path,
                        destination_full_path=destination_full_path,
                        client=client, folder_id=folder_id)


if __name__ == '__main__':
    main()
