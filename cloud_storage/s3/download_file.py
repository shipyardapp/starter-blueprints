import os
import boto3
import botocore
from botocore.client import Config
import re
import argparse
import code


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket-name', dest='bucket_name', required=True)
    parser.add_argument('--s3-file-name-match-type', dest='s3_file_name_match_type',
                        choices={'exact_match', 'regex_match'}, required=True)
    parser.add_argument('--s3-folder-prefix',
                        dest='s3_folder_prefix', default='', required=False)
    parser.add_argument('--s3-file-name', dest='s3_file_name', required=True)
    parser.add_argument('--destination-file-name',
                        dest='destination_file_name', default=None, required=False)
    parser.add_argument('--destination-folder-name',
                        dest='destination_folder_name', default='', required=False)
    parser.add_argument('--s3-config', dest='s3_config',
                        default=None, required=False)
    return parser.parse_args()


def connect_to_s3(s3_config=None):
    """
    Create a connection to the S3 service using credentials provided as environment variables.
    """
    s3_connection = boto3.client(
        's3',
        config=Config(s3_config)
    )
    return s3_connection


def extract_file_name_from_s3_key_name(s3_key_name):
    """
    Use the file name provided in the s3_file_name variable. Should be run only
    if a destination_file_name is not provided.
    """
    destination_file_name = os.path.basename(s3_key_name)
    return destination_file_name


def enumerate_destination_file_name(destination_file_name, file_number=1):
    destination_file_name = re.sub(
        r'\.', f'_{file_number}.', destination_file_name, 1)
    return destination_file_name


def determine_destination_file_name(*, s3_key_name, destination_file_name, file_number=None):
    """
    Determine if the destination_file_name was provided, or should be extracted from the s3_file_name, 
    or should be enumerated for multiple file downloads.
    """
    if destination_file_name:
        if file_number:
            destination_file_name = enumerate_destination_file_name(
                destination_file_name, file_number)
        else:
            destination_file_name = destination_file_name
    else:
        destination_file_name = extract_file_name_from_s3_key_name(
            s3_file_name)

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
    combined_name = os.path.join(folder_name, file_name)
    combined_name = os.path.normpath(combined_name)

    return combined_name


def list_s3_objects(s3_connection, bucket_name, prefix='', continuation_token=None):
    """
    List 1000 objects at a time, filtering by the prefix and continuing if more than 1000
    objects were found on the previous run.
    """
    kwargs = {'Bucket': bucket_name, 'Prefix': prefix}
    if continuation_token:
        kwargs['ContinuationToken'] = continuation_token
    return s3_connection.list_objects_v2(**kwargs)


def get_continuation_token(response):
    """
    Determine if a continuation token was provided in the S3 list_objects_v2 response.
    """
    continuation_token = response.get('NextContinuationToken')
    return continuation_token


def find_file_names(response):
    """
    Return all the objects found on S3 as a list.
    """
    file_names = []
    objects = response['Contents']
    for obj in objects:
        object = obj['Key']
        file_names.append(object)

    return file_names


def download_s3_file(s3_connection, bucket_name, s3_key_name, destination_file_name=None):
    """
    Download a selected file from S3 to local storage in the current working directory.
    """
    local_path = os.path.normpath(f'{os.getcwd()}/{destination_file_name}')

    s3_connection.download_file(bucket_name, s3_key_name, local_path)

    print(f'{bucket_name}/{s3_key_name} successfully downloaded to {local_path}')

    return


def find_all_file_names(s3_connection, bucket_name, s3_folder_prefix=''):
    response = list_s3_objects(s3_connection=s3_connection,
                               bucket_name=bucket_name, prefix=s3_folder_prefix)
    file_names = find_file_names(response)
    continuation_token = response.get('NextContinuationToken')

    while continuation_token:
        response = list_s3_objects(
            s3_connection=s3_connection, bucket_name=bucket_name, prefix=s3_folder_prefix, continuation_token=continuation_token)
        file_names = file_names.append(find_file_names(response))
        continuation_token = response.get('NextContinuationToken')
    return file_names


def find_all_file_matches(file_names, file_name_re):
    matching_file_names = []
    for file in file_names:
        if re.search(file_name_re, file):
            matching_file_names.append(file)

    return matching_file_names


def determine_destination_name(destination_folder_name, destination_file_name, s3_key_name, file_number=None):
    destination_file_name = determine_destination_file_name(
        destination_file_name=destination_file_name, s3_key_name=s3_key_name, file_number=file_number)
    destination_name = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)
    return destination_name


def main():
    args = get_args()
    bucket_name = args.bucket_name
    s3_file_name = args.s3_file_name
    s3_folder_prefix = clean_folder_name(args.s3_folder_prefix)
    s3_key_name = combine_folder_and_file_name(
        folder_name=s3_folder_prefix, file_name=s3_file_name)
    s3_file_name_match_type = args.s3_file_name_match_type
    s3_config = args.s3_config
    destination_folder_name = clean_folder_name(args.destination_folder_name)

    if not os.path.exists(destination_folder_name) and (destination_folder_name != ''):
        os.makedirs(destination_folder_name)

    s3_connection = connect_to_s3(s3_config)

    if s3_file_name_match_type == 'regex_match':
        file_names = find_all_file_names(
            s3_connection=s3_connection, bucket_name=bucket_name, s3_folder_prefix=s3_folder_prefix)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(s3_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to download...')

        for index, key_name in matching_file_names:
            determine_destination_name(destination_folder_name=destination_folder_name,
                                       destination_file_name=args.destination_file_name, s3_key_name=key_name, file_number=index+1)
            download_s3_file(bucket_name=bucket_name, s3_key_name=key_name,
                             destination_file_name=destination_name, s3_connection=s3_connection)
    else:
        determine_destination_name(destination_folder_name=destination_folder_name,
                                   destination_file_name=args.destination_file_name, s3_key_name=s3_key_name)
        download_s3_file(bucket_name=bucket_name, s3_key_name=s3_key_name,
                         destination_file_name=destination_name, s3_connection=s3_connection)


if __name__ == '__main__':
    main()
