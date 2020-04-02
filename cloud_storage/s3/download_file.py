import os
import boto3
import botocore
from botocore.client import Config
import re
import argparse


def getArgs(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket_name', dest='bucket_name', required=True)
    parser.add_argument('--object_name', dest='object_name', required=True)
    parser.add_argument('--downloaded_file_name',
                        dest='downloaded_file_name', default=None, required=False)
    return parser.parse_args()


def connect_to_s3():
    s3_connection = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        # s3v4 is a required part of using the KMS SSE Keys
        config=Config(signature_version='s3v4')
    )
    return s3_connection


def determine_file_name(object_name):
    """
    Use the file name provided in the object name. Should be run only
    if a new downloaded_file_name is not provided. 
    """
    file_name_re = re.compile(r'[\\\/]*([\w\-\._]+)$')
    downloaded_file_name = re.search(file_name_re, object_name).group(1)
    return downloaded_file_name


def download_s3_file(bucket_name='', object_name='', downloaded_file_name=None):

    s3_connection = connect_to_s3()
    cwd = os.getcwd()

    if not downloaded_file_name:
        downloaded_file_name = determine_file_name(object_name)

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
object_name = args.object_name
downloaded_file_name = args.downloaded_file_name

download_s3_file(bucket_name=bucket_name, object_name=object_name,
                 downloaded_file_name=downloaded_file_name)
