# Tutorial file content pulled directly from Great Expecations Docs.
# Visit https://docs.greatexpectations.io/en/latest/getting_started/typical_workflow.html for more examples.
import os
import sys
import argparse
import re
import boto3
import great_expectations as ge
import wget
import pandas as pd
import gzip
import shutil
import uuid


def getArgs(args=None):
    # Pass through arguments that we've set up as Blueprint Variables
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_url', dest='input_url',
                        required=True, type=str)
    parser.add_argument('--output_bucket_name',
                        dest='output_bucket_name', type=str)
    parser.add_argument('--expectation_suite',
                        dest='expectation_suite', required=True, type=str)
    return parser.parse_args()


def extract_file_name(object):
    file_name_re = re.compile(
        r'[\\\/]*([\w\-_]+\.(txt|csv|tsv|psv)(.gz|.zip)*)$')
    file_name = re.search(file_name_re, object).group(1)
    return file_name


def convert_tsv_to_csv(file_name):
    df = pd.read_csv(file_name, sep='\t', error_bad_lines=False)
    updated_file_name = file_name[:-4] + '.csv'
    df.to_csv(updated_file_name, sep=',', index=False)
    return updated_file_name


def decompress_file(file_name):
    with gzip.open(file_name, 'rb') as f_in:
        with open(file_name[:-3], 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    decompressed_file_name = file_name[:-3]
    return decompressed_file_name


def is_compressed(file_name):
    is_compressed = file_name[-3:] == '.gz'
    return is_compressed


def convert_file_name(file_name):
    file_name = file_name[:-3]
    return file_name


def connect_to_s3():
    s3_connection = boto3.client(
        's3',
        aws_access_key_id=os.environ.get(
            'GREAT_EXPECTATIONS_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get(
            'GREAT_EXPECTATIONS_AWS_SECRET_ACCESS_KEY')
    )
    return s3_connection


def upload_to_s3(local_file_name, bucket_name, upload_file_name):
    s3_connection = connect_to_s3()
    s3_upload_config = boto3.s3.transfer.TransferConfig()
    s3_transfer = boto3.s3.transfer.S3Transfer(
        client=s3_connection, config=s3_upload_config)
    s3_transfer.upload_file(local_file_name,
                            bucket_name, upload_file_name)


# Set arguments as variables
args = getArgs()
input_url = args.input_url
output_bucket_name = args.output_bucket_name
expectation_suite = args.expectation_suite

# Creates unique ID combination using Shipyard's Platform Environment Variables
project_id = os.environ.get('SHIPYARD_PROJECT_ID', 'local'+str(uuid.uuid4()))
vessel_id = os.environ.get('SHIPYARD_VESSEL_ID', 'local'+str(uuid.uuid4()))
log_id = os.environ.get('SHIPYARD_LOG_ID', 'local'+str(uuid.uuid4()))
run_id = f'{project_id}_{vessel_id}_{log_id}'


file_name = extract_file_name(input_url)
wget.download(input_url, file_name)

if is_compressed(file_name):
    decompress_file(file_name)
    file_name = convert_file_name(file_name)

file_name = convert_tsv_to_csv(file_name)

# Data Context is a GE object that represents your project.
# Your project's great_expectations.yml contains all the config
# options for the project's GE Data Context.
context = ge.data_context.DataContext()

datasource_name = "root"  # a datasource configured in your great_expectations.yml

# Tell GE how to fetch the batch of data that should be validated...

# ... from a file:
batch_kwargs = {"path": file_name, "datasource": datasource_name}

# Get the batch of data you want to validate.
# Specify the name of the expectation suite that holds the expectations.
expectation_suite_name = expectation_suite   # this is the name of
# the suite we created
batch = context.get_batch(batch_kwargs, expectation_suite_name)

# Call a validation operator to validate the batch.
# The operator will evaluate the data against the expectations
# and perform a list of actions, such as saving the validation
# result, updating Data Docs, and firing a notification (e.g., Slack).
results = context.run_validation_operator(
    "action_list_operator",
    assets_to_validate=[batch],
    run_id=run_id)  # e.g., Shipyard log id, plus additional identifiers.

validation_path = os.path.join(
    os.getcwd(), f'great_expectations/uncommitted/validations/{expectation_suite}/{run_id}/')
validation_file = os.listdir(validation_path)[0]
validation_file_path = os.path.join(validation_path, validation_file)

if output_bucket_name:
    upload_to_s3(validation_file_path, output_bucket_name,
                 f'great-expectations/{expectation_suite}/{run_id}.json')

# Printing so we'll have a record of the output stored in the Shipyard Log.
print(results)

if not results["success"]:
    sys.exit(1)
