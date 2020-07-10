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
    parser.add_argument('--dataset', dest='dataset', required=True)
    parser.add_argument('--table', dest='table', required=True)
    parser.add_argument('--service-account', dest='service_account', required=True)
    parser.add_argument('--source-file-name', dest='source_file_path',
            default='output.csv', required=True)
    parser.add_argument('--source-folder-name',
            dest='source_folder_name', default='', required=False)
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


def copy_from_csv(client, dataset, table, source_file_path):
    """
    Copy CSV data into Bigquery table.
    """
    try:
        dataset_ref = client.dataset(dataset)
        table_ref = dataset_ref.table(table)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.CSV
        job_config.skip_leading_rows = 1
        job_config.autodetect = True
        with open(source_file_path, 'rb') as source_file:
            job = client.load_table_from_file(source_file, table_ref,
                                                job_config=job_config)
        job.result()
    except Exception as e:
        print(f'Failed to copy CSV {source_file_path} to bigquery.')
        raise(e)

    print(f'Successfully copied csv {source_file_path} to bigquery')


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
    dataset = args.dataset
    table = args.table
    source_file_path = args.source_file_path
    source_folder_name = args.source_folder_name
    source_full_path = combine_folder_and_file_name(
        folder_name=source_folder_name, file_name=source_file_path)

    if not os.path.isfile(source_full_path):
        print(f'File {source_full_path} does not exist')
        return

    if tmp_file:
        client = get_client(tmp_file)
    else:
        client = get_client(args.service_account)

    copy_from_csv(client=client, dataset=dataset, table=table,
                    source_file_path=source_file_path)

    if tmp_file:
        print(f'Removing temporary credentials file {tmp_file}')
        os.remove(tmp_file)


if __name__ == '__main__':
    main()
