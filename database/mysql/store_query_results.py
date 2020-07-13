import mysql.connector
import argparse
import os
import pandas as pd


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument('--password', dest='password', required=False)
    parser.add_argument('--host', dest='host', required=True)
    parser.add_argument('--database', dest='database', required=True)
    parser.add_argument('--port', dest='port', default='3306', required=False)
    parser.add_argument('--query', dest='query', required=True)
    parser.add_argument('--destination-file-name', dest='destination_file_name',
            default='output.csv', required=True)
    parser.add_argument('--destination-folder-name',
            dest='destination_folder_name', default='', required=False)
    parser.add_argument('--file-header', dest='file_header', default='True',
            required=False)
    args = parser.parse_args()
    return args


def convert_to_boolean(string):
    """
    Shipyard can't support passing Booleans to code, so we have to convert
    string values to their boolean values.
    """
    if string in ['True', 'true', 'TRUE']:
        value = True
    else:
        value = False
    return value


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')

    return combined_name


def create_csv(query, db_connection, destination_file_path, file_header=True):
    """
    Read in data from a SQL query. Store the data as a csv.
    """
    i = 1
    for chunk in pd.read_sql_query(query, db_connection, chunksize=10000):
        if i == 1:
            chunk.to_csv(destination_file_path, mode='a',
                         header=file_header, index=False)
        else:
            chunk.to_csv(destination_file_path, mode='a',
                         header=False, index=False)
        i += 1
    return


def main():
    args = get_args()
    username = args.username
    password = args.password
    host = args.host
    database = args.database
    port = args.port
    destination_file_name = args.destination_file_name
    destination_folder_name = args.destination_folder_name
    destination_full_path = combine_folder_and_file_name(
        folder_name=destination_folder_name, file_name=destination_file_name)
    file_header = convert_to_boolean(args.file_header)
    query = args.query

    db = mysql.connector.connect(host=host, port=int(port), user=username,
                                passwd=password, database=database,
                                autocommit=True)

    if not os.path.exists(destination_folder_name) and (
            destination_folder_name != ''):
        os.makedirs(destination_folder_name)

    create_csv(
        query=query,
        db_connection=db,
        destination_file_path=destination_full_path,
        file_header=file_header)


if __name__ == '__main__':
    main()
