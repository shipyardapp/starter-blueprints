import argparse
import os
import pandas as pd
import code
from simple_salesforce import Salesforce

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username',
                        dest='username', required=True)
    parser.add_argument('--password',
                        dest='password', required=True)
    parser.add_argument('--security-token',
                        dest='security_token', required=True)               
    parser.add_argument('--object-name',
                        dest='object_name', required=True)
    parser.add_argument('--action', choices=['insert','update','upsert','delete'])
    parser.add_argument('--source-file-name',
                        dest='source_file_name',required=True)
    parser.add_argument('--source-folder-name',
                        dest='source_folder_name', default='', required=False)
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
    action = args.action
    object_name = args.object_name
    source_file_name = args.source_file_name
    source_folder_name = clean_folder_name(args.source_folder_name)
    source_full_path = combine_folder_and_file_name(
        source_folder_name, source_file_name)

    sf_connection = Salesforce(
    username=username, 
    password=password, 
    security_token=security_token,
    client_id='Shipyard')

    df = pd.read_csv(source_full_path)
    data_as_dict = df.to_dict(orient='records')

    command = f"sf_connection.bulk.{object_name}.{action}(data_as_dict,batch_size=10000,use_serial=True)"
    code.interact(local=locals())
    eval(command)

if __name__ == '__main__':
    main()
