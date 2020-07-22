import os
import json
import tempfile
import argparse
import re

import pandas as pd

from google.cloud import bigquery
from google.oauth2 import service_account
from google.api_core.exceptions import BadRequest


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', dest='query', required=True)
    parser.add_argument('--service-account',
                        dest='service_account', required=True)
    parser.add_argument('--bucket-name', dest='bucket_name', required=True)
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


def enumerate_destination_file_name(destination_file_name):
    """
    Append a * to the end of the provided destination file name.
    Only used when query output is too big and Google returns an error
    requesting multiple file names.
    """
    if re.search(r'\.', destination_file_name):
        destination_file_name = re.sub(
            r'\.', f'_*.', destination_file_name, 1)
    else:
        destination_file_name = f'{destination_file_name}_*'
    return destination_file_name


def run_query(query, client):
    """
    Read in data from a SQL query and return the temporary table Bigquery generated with results.
    """
    try:
        data = client.query(query)
        data.result() # Wait for completion
        temp_table_ids = data._properties["configuration"]["query"]["destinationTable"]
        location = data._properties["jobReference"]["location"]
        project_id = temp_table_ids.get('projectId')
        dataset_id = temp_table_ids.get('datasetId')
        table_id = temp_table_ids.get('tableId')
    except Exception as e:
        print(f'Failed to execute your query: {query}')
        raise(e)
    return project_id, dataset_id, table_id, location


def store_temp_table_to_gcs(project_id, dataset_id, table_id, location, bucket_name, destination_full_path, client):

    destination_uri = f'gs://{bucket_name}/{destination_full_path}'
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    table_ref = dataset_ref.table(table_id)

    try:
        extract_job = client.extract_table(
            table_ref,
            destination_uri,
            location="US")

        extract_job.result()
    except BadRequest as e:

        destination_uri = f'gs://{bucket_name}/{enumerate_destination_file_name(destination_full_path)}'
        extract_job = client.extract_table(
            table_ref,
            destination_uri,
            location="US")
    except Exception as e:
        raise(e)

    print(f'Successfully exported your query to {destination_uri}')


def get_client(credentials):
    """
    Attempts to create the Google Bigquery Client with the associated
    environment variables
    """
    try:
        client = bigquery.Client()
        return client
    except Exception as e:
        print(f'Error accessing Google Drive with service account '
              f'{credentials}')
        raise(e)


def main():
    args = get_args()
    tmp_file = set_environment_variables(args)
    bucket_name = args.bucket_name
    destination_file_name = args.destination_file_name
    destination_folder_name = args.destination_folder_name
    destination_full_path = combine_folder_and_file_name(
        folder_name=destination_folder_name, file_name=destination_file_name)
    query = args.query

    if tmp_file:
        client = get_client(tmp_file)
    else:
        client = get_client(args.service_account)

    project_id, dataset_id, table_id, location = run_query(
        query=query, client=client)
    print('Query finished successfully. Storing results on GCS.')
    store_temp_table_to_gcs(project_id=project_id, dataset_id=dataset_id, table_id=table_id,
                            location=location, bucket_name=bucket_name, destination_full_path=destination_full_path, client=client)

    if tmp_file:
        print(f'Removing temporary credentials file {tmp_file}')
        os.remove(tmp_file)


if __name__ == '__main__':
    main()
