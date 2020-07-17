from sqlalchemy import create_engine
import argparse
import os
import glob
import re
import pandas as pd


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument('--password', dest='password', required=False)
    parser.add_argument('--host', dest='host', required=True)
    parser.add_argument('--database', dest='database', required=True)
    parser.add_argument('--port', dest='port', default='3306', required=False)
    parser.add_argument('--url-parameters',
                        dest='url_parameters', required=False)
    parser.add_argument('--source-file-name-match-type',
                        dest='source_file_name_match_type',
                        choices={
                            'exact_match',
                            'regex_match'},
                        required=True)
    parser.add_argument('--source-file-name', dest='source_file_name',
                        default='output.csv', required=True)
    parser.add_argument('--source-folder-name',
                        dest='source_folder_name', default='', required=False)
    parser.add_argument('--file-header', dest='file_header', default='True',
                        required=False)
    parser.add_argument('--table-name', dest='table_name', default=None,
                        required=True)
    parser.add_argument('--insert-method', dest='insert_method', choices={'fail', 'replace', 'append'}, default='append',
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


def find_all_local_file_names(source_folder_name):
    """
    Returns a list of all files that exist in the current working directory,
    filtered by source_folder_name if provided.
    """
    cwd = os.getcwd()
    cwd_extension = os.path.normpath(f'{cwd}/{source_folder_name}/**')
    file_names = glob.glob(cwd_extension, recursive=True)
    return [file_name for file_name in file_names if os.path.isfile(file_name)]


def find_all_file_matches(file_names, file_name_re):
    """
    Return a list of all file_names that matched the regular expression.
    """
    matching_file_names = []
    for file in file_names:
        if re.search(file_name_re, file):
            matching_file_names.append(file)

    return matching_file_names


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')

    return combined_name


def upload_data(source_full_path, table_name, insert_method, db_connection):
    for chunk in pd.read_csv(source_full_path, chunksize=10000):
        chunk.to_sql(table_name, con=db_connection, index=False,
                     if_exists=insert_method, chunksize=10000)


def main():
    args = get_args()
    username = args.username
    password = args.password
    host = args.host
    database = args.database
    port = args.port
    source_file_name_match_type = args.source_file_name_match_type
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    source_full_path = combine_folder_and_file_name(
        folder_name=source_folder_name, file_name=source_file_name)
    file_header = convert_to_boolean(args.file_header)
    url_parameters = args.url_parameters
    table_name = args.table_name
    insert_method = args.insert_method

    db_string = f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}?{url_parameters}'
    db_connection = create_engine(
        db_string, pool_recycle=3600, execution_options=dict(
            stream_results=True))

    if source_file_name_match_type == 'regex_match':
        file_names = find_all_local_file_names(source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to upload...')

        for index, key_name in enumerate(matching_file_names):
            upload_data(source_full_path=key_name, table_name=table_name,
                        insert_method=insert_method, db_connection=db_connection)
            print(f'{key_name} has been uploaded to {table_name}.')

    else:
        upload_data(source_full_path=source_full_path, table_name=table_name,
                    insert_method=insert_method, db_connection=db_connection)


if __name__ == '__main__':
    main()
