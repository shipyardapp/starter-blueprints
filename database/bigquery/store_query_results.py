import os
import json
import tempfile
import argparse

import pandas as pd

from google.cloud import bigquery
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', dest='query', required=True)
    parser.add_argument('--service-account', dest='service_account', required=True)
    parser.add_argument('--destination-file-name', dest='destination_file_name',
            default='output.csv', required=True)
    parser.add_argument('--destination-folder-name',
            dest='destination_folder_name', default='', required=False)
    args = parser.parse_args()
    return args


def set_environment_variables(args):
    """
    Set GCP credentials as environment variables if they're provided via keyword
    arguments rather than seeded as environment variables. This will override
    system defaults.
    """
    credentials = args.service_account
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


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')

    return combined_name


def create_csv(query, client, destination_file_path):
    """
    Read in data from a SQL query. Store the data as a csv.
    """
    try:
        data = client.query(query).to_dataframe()
    except Exception as e:
        print(f'Failed to execute your query: {query}')
        raise(e)

    try:
        data.to_csv(destination_file_path)
    except Exception as e:
        print(f'Failed to write the data to csv {destination_file_path}')
        raise(e)

    print(f'Successfully stored query results to {destination_file_path}')


def get_client(credentials):
    """
    Attempts to create the Google Drive Client with the associated
    environment variables
    """
    try:
        client = bigquery.Client()
        return client
    except Exception as e:
        print(f'Error accessing Google Drive with service account ' \
                f'{credentials}')
        raise(e)


def main():
    args = get_args()
    tmp_file = set_environment_variables(args)
    destination_file_name = args.destination_file_name
    destination_folder_name = args.destination_folder_name
    destination_full_path = combine_folder_and_file_name(
        folder_name=destination_folder_name, file_name=destination_file_name)
    query = args.query

    if tmp_file:
        client = get_client(tmp_file)
    else:
        client = get_client(args.service_account)


    if not os.path.exists(destination_folder_name) and (
            destination_folder_name != ''):
        os.makedirs(destination_folder_name)

    create_csv(query=query, client=client,
            destination_file_path=destination_full_path)

    if tmp_file:
        print(f'Removing temporary credentials file {tmp_file}')
        os.remove(tmp_file)


if __name__ == '__main__':
    main()
