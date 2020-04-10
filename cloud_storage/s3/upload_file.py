import os
import boto3
import botocore
from botocore.client import Config
import re
import argparse


def getArgs(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket_name', dest='bucket_name', required=True)
    parser.add_argument('--local-file-name-match-type', dest='local_file_name_match_type',
                        choices={'exact_match', 'regex_match'}, required=True)
    parser.add_argument('--prefix', dest='prefix', default='', required=False)
    parser.add_argument('--source-file-name',
                        dest='local_file_name', required=True)
    parser.add_argument('--source-folder-name',
                        dest='local_folder_name', required=True)
    parser.add_argument('--destination-folder-name',
                        dest='destination_folder_name', default=None, required=False)
    parser.add_argument('--destination-file-name',
                        dest='destination_file_name', default=None, required=False)
    parser.add_argument('--s3-config', dest='s3_config',
                        default=None, required=False)
    parser.add_argument('--s3-extra-args', dest='s3_extra_args',
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


def extract_file_name_from_source_full_path(source_full_path):
    """
    Use the file name provided in the source_file_name variable. Should be run only
    if a destination_file_name is not provided.
    """
    destination_file_name = os.path.basename(source_full_path)
    return destination_file_name


def enumerate_destination_file_name(destination_file_name, file_number=1):
    """
    Append a number to the end of the provided destination file name.
    Only used when multiple files are matched to, preventing the destination file from being continuously overwritten.
    """
    destination_file_name = re.sub(
        r'\.', f'_{file_number}.', destination_file_name, 1)
    return destination_file_name


def determine_destination_file_name(*, source_full_path, destination_file_name, file_number=None):
    """
    Determine if the destination_file_name was provided, or should be extracted from the source_file_name, 
    or should be enumerated for multiple file downloads.
    """
    if destination_file_name:
        if file_number:
            destination_file_name = enumerate_destination_file_name(
                destination_file_name, file_number)
        else:
            destination_file_name = destination_file_name
    else:
        destination_file_name = extract_file_name_from_source_full_path(
            source_full_path)

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


def determine_destination_name(destination_folder_name, destination_file_name, source_full_path, file_number=None):
    """
    Determine the final destination name of the file being downloaded.
    """
    destination_file_name = determine_destination_file_name(
        destination_file_name=destination_file_name, source_full_path=source_full_path, file_number=file_number)
    destination_name = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)
    return destination_name


def upload_s3_file(file_name='', folder_name='', object_name='', bucket_name='', extra_args=None, s3_connection=None):
    """
    Uploads a single file to S3. Uses the s3.transfer method to ensure that files larger than 5GB are split up during the upload process.

    Extra Args can be found at https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter
    and are commonly used for custom file encryption or permissions.
    """
    s3_upload_config = boto3.s3.transfer.TransferConfig()
    s3_transfer = boto3.s3.transfer.S3Transfer(
        client=s3_connection, config=s3_upload_config)

    if folder_name:
        object_name = combine_folder_and_file_name(folder_name, object_name)

    s3_transfer.upload_file(file_name, bucket_name,
                            object_name, extra_args=extra_args)

    print(f'{file_name} successfully uploaded to {bucket_name}{folder_name or "/"}{object_name}')


def main():
    args = getArgs()
    bucket_name = args.bucket_name
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    destination_file_name = args.destination_file_name
    destination_folder_name = args.destination_folder_name
    object_name = determine_object_name(args)
    source_file_name_match_type = args.source_file_name_match_type
    s3_config = args.s3_config
    extra_args = args.extra_args

    s3_connection = connect_to_s3(s3_config)

    if source_file_name_match_type == 'regex_match':
        file_names = find_all_s3_file_names(
            s3_connection=s3_connection, bucket_name=bucket_name, source_folder_name=source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to download...')

        for index, key_name in enumerate(matching_file_names):
            destination_name = determine_destination_name(destination_folder_name=destination_folder_name,
                                                          destination_file_name=args.destination_file_name, source_full_path=key_name, file_number=index+1)
            print(f'Uploading file {index+1} of {len(matching_file_names)}')
            upload_s3_file(file_name=key_name, folder_name=destination_folder_name, object_name=object_name_enumerated,
                           bucket_name=bucket_name, extra_args=extra_args, s3_connection=s3_connection)

    else:
        destination_name = determine_destination_name(destination_folder_name=destination_folder_name,
                                                      destination_file_name=args.destination_file_name, source_full_path=key_name, file_number=index+1)
        upload_s3_file(file_name=local_file_name, folder_name=prefix, object_name=object_name,
                       bucket_name=bucket_name, extra_args=extra_args, s3_connection=s3_connection)


if __name__ == '__main__':
    main()
