import os
import json
import tempfile
import argparse

from google.cloud import bigquery
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', dest='query', required=True)
    parser.add_argument('--service-account', dest='service_account', required=True)
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
    query = args.query

    if tmp_file:
        client = get_client(tmp_file)
    else:
        client = get_client(args.service_account)

    try:
        job = client.query(query)
        result = job.result()
    except Exception as e:
        print('Failed to execute your query')
        raise(e)

    print('Your query has been successfully executed.')

    if tmp_file:
        print(f'Removing temporary credentials file {tmp_file}')
        os.remove(tmp_file)


if __name__ == '__main__':
    main()
