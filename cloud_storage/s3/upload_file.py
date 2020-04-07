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
    """
    Check to see if the folder name ends with a slash. Return a regex match object.
    """
    folder_name = str(folder_name)
    extensions = re.compile(r'\/$')
    match = extensions.search(folder_name)
    return match


def generate_full_folder_name(folder_name):
    """
    Add a trailing slash to the folder if it was missing one.
    """
    folder_name = str(folder_name)
    if check_folder_name_ends_with_slash(folder_name):
        pass
    else:
        folder_name = folder_name + '/'
    return folder_name


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine the folder name and file name together to create the _true_ object name.
    """
    folder_name = generate_full_folder_name(folder_name)
    object_name = f'{folder_name}{file_name}'
    return object_name


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


def determine_object_name(args):
    """
    Determine if the object name was provided or should be extracted from the local_file_name.
    """
    if not args.object_name:
        if args.quantity == 'individual':
            object_name = local_file_name
        else:
            object_name = args.object_name
    else:
        object_name = args.object_name
    return object_name


def main():
    args = getArgs()
    bucket_name = args.bucket_name
    local_file_name = args.local_file_name
    object_name = determine_object_name(args)
    quantity = args.quantity
    prefix = args.prefix
    extra_args = args.extra_args

    s3_connection = connect_to_s3()

    if quantity == 'multiple':
        file_name_re = re.compile(local_file_name)
        i = 1

        local_files = os.listdir()
        for file in local_files:
            if re.search(file_name_re, file):

                if object_name:
                    if '.' in object_name:
                        object_name_enumerated = re.sub(
                            r'\.', f'_{i}.', object_name, 1)
                    else:
                        object_name_enumerated = f'{object_name}_{i}'

                else:
                    object_name_enumerated = file
                upload_s3_file(file_name=file, folder_name=prefix, object_name=object_name_enumerated,
                               bucket_name=bucket_name, extra_args=extra_args, s3_connection=s3_connection)
                i += 1
    else:
        upload_s3_file(file_name=local_file_name, folder_name=prefix, object_name=object_name,
                       bucket_name=bucket_name, extra_args=extra_args, s3_connection=s3_connection)


if __name__ == '__main__':
    main()
