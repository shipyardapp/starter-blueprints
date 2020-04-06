import os
import boto3
import botocore
from botocore.client import Config
import re
import argparse


def getArgs(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket_name', dest='bucket_name', required=True)
    parser.add_argument('--quantity', dest='quantity',
                        choices={'individual', 'multiple'}, required=True)
    parser.add_argument('--prefix', dest='prefix', default='', required=False)
    parser.add_argument('--local_file_name',
                        dest='local_file_name', required=True)
    parser.add_argument('--extra_args', dest='extra_args',
                        default=None, required=False)
    parser.add_argument('--object_name',
                        dest='object_name', default=None, required=False)
    return parser.parse_args()


def connect_to_s3():
    """
    Create a connection to the S3 service using credentials provided as environment variables.
    """
    s3_connection = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        # s3v4 is a required part of using the KMS SSE Keys
        config=Config(signature_version='s3v4')
    )
    return s3_connection


def check_folder_name_ends_with_slash(folder_name):
    folder_name = str(folder_name)
    extensions = re.compile(r'\/$')
    match = extensions.search(folder_name)
    return match


def generate_full_folder_name(folder_name):
    folder_name = str(folder_name)
    if check_folder_name_ends_with_slash(folder_name):
        pass
    else:
        folder_name = folder_name + '/'
    return folder_name


def combine_folder_and_file_name(folder_name, file_name):
    folder_name = generate_full_folder_name(folder_name)
    object_name = f'{folder_name}{file_name}'
    return object_name


def upload_s3_file(file_name='', folder_name='', object_name='', bucket_name='', extra_args=None, s3_connection=None):
    s3_upload_config = boto3.s3.transfer.TransferConfig()
    s3_transfer = boto3.s3.transfer.S3Transfer(
        client=s3_connection, config=s3_upload_config)

    if folder_name:
        object_name = combine_folder_and_file_name(folder_name, object_name)

    s3_transfer.upload_file(file_name, bucket_name,
                            object_name, extra_args=extra_args)


def determine_object_name(args):
    """
    Determine if the object name was provided or should be extracted from the local_file_name.
    """
    if not args.object_name:
        if args.quantity == 'individual':
            object_name = local_file_name
    else:
        object_name = args.downloaded_file_name
    return object_name


args = getArgs()
bucket_name = args.bucket_name
local_file_name = args.local_file_name
object_name = determine_object_name(args)
quantity = args.quantity
prefix = args.prefix
extra_args = args.extra_args

s3_connection = connect_to_s3()

if quantity == 'multiple':
    pass
else:
    upload_s3_file(file_name=local_file_name, folder_name=prefix, object_name=object_name,
                   bucket_name=bucket_name, extra_args=extra_args, s3_connection=s3_connection)
