import os
import boto3
import botocore
from botocore.client import Config
import re
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket-name', dest='bucket_name', required=True)
    parser.add_argument('--s3-file-name-match-type', dest='s3_file_name_match_type',
                        choices={'exact_match', 'regex_match'}, required=True)
    parser.add_argument('--s3-folder-prefix',
                        dest='s3-folder-prefix', default='', required=False)
    parser.add_argument('--s3-file-name', dest='s3_file_name', required=True)
    parser.add_argument('--destination-file-name',
                        dest='destination_file_name', default=None, required=False)
    parser.add_argument('--s3-config', dest='s3_config',
                        default=None, required=False)
    return parser.parse_args()


def connect_to_s3():
    """
    Create a connection to the S3 service using credentials provided as environment variables.
    """
    s3_connection = boto3.client(
        's3',
        config=Config(s3_config)
    )
    return s3_connection


def extract_file_name_from_object(s3_file_name):
    """
    Use the file name provided in the object name. Should be run only
    if a new destination_file_name is not provided. 
    """
    file_name_re = re.compile(r'[\\\/]*([\w\-\._]+)$')
    destination_file_name = re.search(file_name_re, s3_file_name).group(1)
    return destination_file_name


def determine_file_name(args):
    """
    Determine if the file name was provided or should be extracted from the s3_file_name.
    """
    if not args.destination_file_name:
        if args.s3_file_name_match_type == 'exact_match':
            destination_file_name = extract_file_name_from_object(
                args.s3_file_name)
    else:
        destination_file_name = args.destination_file_name
    return destination_file_name


def clean_s3_file_name(s3_file_name):
    """
    Prevent objects provided with / at the beginning from causing errors.
    """
    if s3_file_name[0] == '/':
        s3_file_name = s3_file_name[1:]
    return s3_file_name


def list_s3_objects(bucket_name='', prefix='', continuation_token='', s3_connection=None):
    """
    List 1000 objects at a time, filtering by the prefix and continuing if more than 1000 
    objects were found on the previous run.
    """
    if continuation_token:
        response = s3_connection.list_objects_v2(
            Bucket=bucket_name, Prefix=prefix, ContinuationToken=continuation_token)
    else:
        response = s3_connection.list_objects_v2(
            Bucket=bucket_name, Prefix=prefix)
    return response


def does_continuation_token_exist(response):
    """
    Determine if a continuation token was provided in the S3 list_objects_v2 response.
    """
    continuation_token = response.get('NextContinuationToken', '')
    return continuation_token


def find_all_file_names(response, file_names=[]):
    """
    Return all the objects found on S3 as a list.
    """
    objects = response['Contents']
    for obj in objects:
        object = obj['Key']
        file_names.append(object)

    return file_names


def download_s3_file(bucket_name='', s3_file_name='', destination_file_name=None, s3_connection=None):
    """
    Download a selected file from S3 to local storage in the current working directory.
    """
    local_path = os.path.normpath(f'{os.getcwd()}/{download_file_name}')

    try:
        s3_connection.download_file(
            bucket_name, s3_file_name, local_path)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print(e.response)
            print(f'{bucket_name}/{s3_file_name} does not exist')
            return
        if e.response['Error']['Code'] == "403":
            print(e.response)
            print(f'You don\'t have access to {bucket_name}/{s3_file_name}')
            return
        else:
            raise

    print(bucket_name+"/"+s3_file_name+" successfully downloaded to " +
          local_path)

    return


def main():
    args = get_args()
    bucket_name = args.bucket_name
    s3_file_name = clean_s3_file_name(args.s3_file_name)
    destination_file_name = determine_file_name(args)
    s3_file_name_match_type = args.s3_file_name_match_type
    prefix = args.prefix

    s3_connection = connect_to_s3()

    if s3_file_name_match_type == 'regex_match':
        response = list_s3_objects(
            bucket_name=bucket_name, prefix=prefix, s3_connection=s3_connection)
        file_names = find_all_file_names(response, file_names=[])
        continuation_token = does_continuation_token_exist(response)

        while continuation_token:
            response = list_s3_objects(
                bucket_name=bucket_name, prefix=prefix, continuation_token=continuation_token)
            file_names = find_all_file_names(response, file_names=file_names)
            continuation_token = does_continuation_token_exist(response)

        s3_file_name_re = re.compile(s3_file_name)
        i = 1
        for file in file_names:
            if re.search(s3_file_name_re, file):

                if destination_file_name:
                    destination_file_name_enumerated = re.sub(
                        r'\.', f'_{i}.', destination_file_name, 1)
                else:
                    destination_file_name = extract_file_name_from_object(file)
                download_s3_file(bucket_name=bucket_name, s3_file_name=file,
                                 destination_file_name=destination_file_name_enumerated, s3_connection=s3_connection)
                i += 1
    else:
        download_s3_file(bucket_name=bucket_name, s3_file_name=s3_file_name,
                         destination_file_name=destination_file_name, s3_connection=s3_connection)


if __name__ is '__main__':
    main()
