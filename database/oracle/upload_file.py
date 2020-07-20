from sqlalchemy import create_engine, types
import argparse
import os
import glob
import re
import pandas as pd
import requests
import cx_Oracle
from zipfile import ZipFile
import platform


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument('--password', dest='password', required=False)
    parser.add_argument('--host', dest='host', required=True)
    parser.add_argument('--database', dest='database', required=False)
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
    parser.add_argument('--table-name', dest='table_name', default=None,
                        required=True)
    parser.add_argument('--insert-method', dest='insert_method', choices={'fail', 'replace', 'append'}, default='append',
                        required=False)
    parser.add_argument('--oracle-location', dest='oracle_location', default=None,
                        required=False)
    args = parser.parse_args()
    return args


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


def determine_os_name(platform):
    if 'macOS' in platform:
        os_name = 'mac'
    elif 'windows' in platform:
        os_name = 'windows'
    else:
        os_name = 'linux'
    return os_name


def determine_os_version(platform):
    if 'x86_64' in platform:
        os_version = '64bit'
    else:
        os_version = '32bit'
    return os_version


def install_oracle_package():
    current_os = platform.platform()
    os_name = determine_os_name(current_os)
    os_version = determine_os_version(current_os)

    oracle_packages = {
        "windows": {
            "64bit": "https://download.oracle.com/otn_software/nt/instantclient/19600/instantclient-basic-windows.x64-19.6.0.0.0dbru.zip",
            "32bit": "https://download.oracle.com/otn_software/nt/instantclient/19600/instantclient-basic-nt-19.6.0.0.0dbru.zip"
        },
        "mac": {
            "64bit": "https://download.oracle.com/otn_software/mac/instantclient/193000/instantclient-basic-macos.x64-19.3.0.0.0dbru.zip",
            "32bit": "https://www.oracle.com/database/technologies/instant-client/macos-x-ppc-downloads.html#license-lightbox"
        },
        "linux": {
            "64bit": "https://download.oracle.com/otn_software/linux/instantclient/19600/instantclient-basic-linux.x64-19.6.0.0.0dbru.zip",
            "32bit": "https://download.oracle.com/otn_software/linux/instantclient/19600//instantclient-basic-linux-19.6.0.0.0dbru.zip"
        }
    }

    if not os.path.exists('./package'):
        os.makedirs('./package')
    url = oracle_packages[os_name][os_version]
    r = requests.get(url, allow_redirects=True)
    open('package/oracle.zip', 'wb').write(r.content)
    with ZipFile('package/oracle.zip', 'r') as zip_file:
        zip_file.extractall('package/oracle')
    return 'package/oracle/instantclient_19_3'


def force_object_dtype_as_object(df):
    """
    Prevents SQLAlchemy from uploading object columns as CLOB.
    Instead forces as varchar, with max length of 4000 bytes.
    This increases upload speed by 40x compared to using CLOB.

    Solution courtesy of:
    https://stackoverflow.com/questions/42727990/speed-up-to-sql-when-writing-pandas-dataframe-to-oracle-database-using-sqlalch
    """
    return {c: types.VARCHAR(4000) for c in df.columns[df.dtypes == 'object'].tolist()}


def upload_data(source_full_path, table_name, insert_method, db_connection):
    for chunk in pd.read_csv(source_full_path, chunksize=10000):
        dtype = force_object_dtype_as_object(chunk)
        chunk.to_sql(table_name, con=db_connection, index=False,
                     if_exists=insert_method, dtype=dtype, chunksize=10000)
    print(f'{source_full_path} was successfully uploaded to {table_name}.')


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
    url_parameters = args.url_parameters
    table_name = args.table_name
    insert_method = args.insert_method
    if args.oracle_location:
        oracle_location = args.oracle_location
    else:
        oracle_location = install_oracle_package()

    cx_Oracle.init_oracle_client(lib_dir=oracle_location)

    db_string = f'oracle+cx_oracle://{username}:{password}@{host}:{port}/{database}?{url_parameters}'
    db_connection = create_engine(
        db_string, execution_options=dict(
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
