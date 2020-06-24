import os
import sys
import re
import json
import argparse

from boxsdk import Client, JWTAuth
from boxsdk.exception import *

import logging
logging.getLogger('boxsdk').setLevel(logging.CRITICAL)


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
    parser.add_argument('--service-account', dest='service_account',
            default=None, required=True)
    return parser.parse_args()


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


def find_box_file_names(client, source_folder_name, source_file_name):
    """
    Fetched all the files in the bucket which are returned in a list of 
    tuples of file_name to file_id
    """
    try:
        if not source_folder_name:
            source_folder_name = '0'

        folders = client.search().query(query=source_folder_name,
                                            result_type='folder')
        search_folder = None
        for folder in folders:
            search_folder = folder
        if not search_folder:
            search_folder = client.folder('0')

        files = search_folder.get_items()
        file_names = []
        for _file in files:
            file_names.append((_file.name, _file.id))
        return file_names
    except (BoxOAuthException, BoxAPIException) as e:
        print(f'The specified folder {source_folder_name} does not exist')
        raise(e)


def find_matching_files(file_blobs, file_name_re):
    """
    Return a list of all file_names that matched the regular expression.
    """
    matching_file_names = []
    for blob in file_blobs:
        if re.search(file_name_re, blob[0]):
            matching_file_names.append(blob)

    return matching_file_names


def download_box_file(file_name, file_id, client, destination_file_name=None):
    """
    Download a selected file from Box to local storage in
    the current working directory.
    """

    local_path = os.path.normpath(f'{os.getcwd()}/{destination_file_name}')

    with open(local_path, 'wb') as new_blob:
        client.file(file_id).download_to(new_blob)

    print(f'{file_name} successfully downloaded to {local_path}')

    return


def get_client(service_account):
    """
    Attempts to create the Box Client with the associated with the credentials.
    """
    try:
        if os.path.isfile(service_account):
            auth = JWTAuth.from_settings_file(service_account)
        else:
            service_dict = json.loads(service_account)
            auth = JWTAuth.from_settings_dictionary(service_dict)

        client = Client(auth)
        client.user().get()
        return client
    except BoxOAuthException as e:
        print(f'Error accessing Box account with pervice account ' \
              f'developer_token={developer_token}; client_id={client_id}; ' \
              f'client_secret={client_secret}')
        raise(e)

def get_file_id(client, source_folder_name, source_file_name):
    """
    Returns the folder id for the Box client if it exists.
    """
    try:
        search_folder = None
        if not source_folder_name:
            search_folder = client.folder('0')
        else:
            folders = client.search().query(query=source_folder_name,
                                                result_type='folder')
            for folder in folders:
                search_folder = folder

        files = client.search().query(query=source_file_name,
                                        ancestor_folders=[search_folder])
        for _file in files:
            return (_file.name, _file.id)
    except (BoxOAuthException, BoxAPIException) as e:
        print(f'The specified folder {destination_folder_name} does not exist')
        raise(e)


def main():
    args = get_args()
    service_account = args.service_account
    source_file_name = args.source_file_name
    source_folder_name = clean_folder_name(args.source_folder_name)
    source_full_path = combine_folder_and_file_name(
        folder_name=source_folder_name, file_name=source_file_name)
    source_file_name_match_type = args.source_file_name_match_type

    destination_folder_name = clean_folder_name(args.destination_folder_name)
    if not os.path.exists(destination_folder_name) and \
            (destination_folder_name != ''):
        os.makedirs(destination_folder_name)

    client = get_client(service_account=service_account)

    if source_file_name_match_type == 'regex_match':
        file_objs = find_box_file_names(client=client,
                                         source_folder_name=source_folder_name,
                                         source_file_name=source_file_name)
        matching_file_names = find_matching_files(file_objs,
                                            re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to download...')

        for index, file_obj in enumerate(matching_file_names):
            file_name, file_id = file_obj
            destination_name = determine_destination_name(
                    destination_folder_name=destination_folder_name,
                    destination_file_name=args.destination_file_name,
                    source_full_path=file_name, file_number=index+1)

            print(f'Downloading file {index+1} of {len(matching_file_names)}')
            download_box_file(file_name=file_name,
                    file_id=file_id,
                    client=client,
                    destination_file_name=destination_name)
    else:
        file_name, file_id = get_file_id(client=client,
                                source_folder_name=source_folder_name,
                                source_file_name=source_file_name)
        destination_name = determine_destination_name(
                destination_folder_name=destination_folder_name,
                destination_file_name=args.destination_file_name,
                source_full_path=source_full_path)

        download_box_file(file_name=source_file_name, file_id=file_id,
                          client=client, destination_file_name=destination_name)


if __name__ == '__main__':
    main()
