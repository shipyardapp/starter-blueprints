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
                        choices={'single', 'multiple'}, required=True)
    parser.add_argument('--prefix', dest='prefix', required=False)
    parser.add_argument('--object_name', dest='object_name', required=True)
    parser.add_argument('--downloaded_file_name',
                        dest='downloaded_file_name', default=None, required=False)
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


def extract_file_name_from_object(object_name):
    """
    Use the file name provided in the object name. Should be run only
    if a new downloaded_file_name is not provided. 
    """
    file_name_re = re.compile(r'[\\\/]*([\w\-\._]+)$')
    downloaded_file_name = re.search(file_name_re, object_name).group(1)
    return downloaded_file_name


def determine_file_name(args):
    """
    Determine if the file name was provided or should be extracted from the object_name.
    """
    if not args.downloaded_file_name:
        downloaded_file_name = extract_file_name_from_object(args.object_name)
    else:
        downloaded_file_name = args.downloaded_file_name
    return downloaded_file_name


def clean_object_name(object_name):
    if object_name[0] == '/':
        object_name = object_name[1:]
    return object_name


def list_s3_objects(bucket_name='', prefix=None, continuation_token=None):
    s3_connection = connect_to_s3()
    response = s3_connection.list_objects_v2(
        Bucket=bucket_name, Prefix=prefix, ContinuationToken=continuation_token)
    return response


def does_continuation_token_exist(response):
    continuation_token = response.get('NextContinuationToken')
    if continuation_token:
        continuation_token_exists = True
    else:
        continuation_token_exists = False
    return continuation_token


def find_all_file_names(response, file_names=[]):
    objects = response['Contents']
    for obj in objects:
        object = obj['Key']
        file_names.append(object)

    if response.get('NextContinuationToken'):
        s3_connection.list_objects_v2(
            Bucket=bucket_name, ContinuationToken=response.get('NextContinuationToken'))

    return file_names


def download_s3_file(bucket_name='', object_name='', downloaded_file_name=None):

    s3_connection = connect_to_s3()
    cwd = os.getcwd()

    try:
        s3_connection.download_file(
            bucket_name, object_name, str(cwd+"/"+downloaded_file_name))

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print(e.response)
            print(f'{bucket_name}/{object_name} does not exist')
            return e
        if e.response['Error']['Code'] == "403":
            print(e.response)
            print(f'You don\'t have access to {bucket_name}/{object_name}')
            return e
        else:
            raise

    print(bucket_name+"/"+object_name+" successfully downloaded to " +
          cwd+"/"+downloaded_file_name)

    downloaded_file_path = os.path.abspath(downloaded_file_name)
    return downloaded_file_path


args = getArgs()
bucket_name = args.bucket_name
object_name = clean_object_name(args.object_name)
downloaded_file_name = determine_file_name(args)
quantity = args.quantity
prefix = args.prefix

if quantity == 'multiple':
    response = list_s3_objects(bucket_name=bucket_name, prefix=prefix)
    file_names = find_all_file_names(response, file_names=[])
    continuation_token = does_continuation_token_exist(response)

    while continuation_token:
        response = list_s3_objects(
            bucket_name=bucket_name, prefix=prefix, continuation_token=continuation_token)
        file_names = find_all_file_names(response, file_names=file_names)
        continuation_token = does_continuation_token_exist(response)

    for file in file_names:
        download_s3_file(bucket_name=bucket_name, object_name=file,
                         downloaded_file_name=downloaded_file_name)
else:
    download_s3_file(bucket_name=bucket_name, object_name=object_name,
                     downloaded_file_name=downloaded_file_name)
