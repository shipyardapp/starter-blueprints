import argparse
import os
import pandas as pd
from simple_salesforce import Salesforce


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username',
                        dest='username', required=True)
    parser.add_argument('--password',
                        dest='password', required=True)
    parser.add_argument('--security-token',
                        dest='security_token', required=True)
    parser.add_argument('--query',
                        dest='query', required=True)
    parser.add_argument(
        '--destination-file-name',
        dest='destination_file_name',
        default='output.csv',
        required=False)
    parser.add_argument(
        '--destination-folder-name',
        dest='destination_folder_name',
        default='',
        required=False)
    return parser.parse_args()


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')
    combined_name = os.path.normpath(combined_name)

    return combined_name


def clean_folder_name(folder_name):
    """
    Cleans folders name by removing duplicate '/' as well as leading and trailing '/' characters.
    """
    folder_name = folder_name.strip('/')
    if folder_name != '':
        folder_name = os.path.normpath(folder_name)
    return folder_name


def main():
    args = get_args()
    username = args.username
    password = args.password
    security_token = args.security_token
    query = args.query
    destination_file_name = args.destination_file_name
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    destination_name = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)

    if not os.path.exists(destination_folder_name) and \
            (destination_folder_name != ''):
        os.makedirs(destination_folder_name)

    sf_connection = Salesforce(
        username=username,
        password=password,
        security_token=security_token,
        client_id='Shipyard')

    sf_data = sf_connection.query_all(query)
    sf_df = pd.DataFrame(sf_data['records']).drop(columns='attributes')
    sf_df.to_csv(destination_name, index=False)


if __name__ == '__main__':
    main()
