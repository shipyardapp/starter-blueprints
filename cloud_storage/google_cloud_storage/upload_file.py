import os
import sys
import re
import argparse
import glob

from gcloud import storage
from gcloud.exceptions import *


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket-name', dest='bucket_name', required=True)
    parser.add_argument('--force-bucket-creation', dest='force_create',
            default=False, required=False)
    parser.add_argument('--source-file-name-match-type',
            dest='source_file_name_match_type',
            choices={
                'exact_match',
                'regex_match'},
            required=True)
    parser.add_argument('--source-file-name', dest='source_file_name',
            required=True)
    parser.add_argument('--source-folder-name', dest='source_folder_name',
            default='', required=False)
    parser.add_argument('--destination-folder-name',
            dest='destination_folder_name', default='', required=False)
    parser.add_argument('--destination-file-name', dest='destination_file_name',
            default=None, required=False)
    parser.add_argument('--service-account', dest='gcp_application_credentials',
            default=None, required=True)
    return parser.parse_args()


def set_environment_variables(args):
    """
    Set GCP credentials as environment variables if they're provided via keyword
    arguments rather than seeded as environment variables. This will override
    system defaults.
    """
    if args.gcp_application_credentials:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = args.gcp_application_credentials
    return


def extract_file_name_from_source_full_path(source_full_path):
    """
    Use the file name provided in the source_full_path variable. Should be run
    only if a destination_file_name is not provided.
    """
    destination_file_name = os.path.basename(source_full_path)
    return destination_file_name


def enumerate_destination_file_name(destination_file_name, file_number=1):
    """
    Append a number to the end of the provided destination file name.
    Only used when multiple files are matched to, preventing the destination
    file from being continuously overwritten.
    """
    if re.search(r'\.', destination_file_name):
        destination_file_name = re.sub(
            r'\.', f'_{file_number}.', destination_file_name, 1)
    else:
        destination_file_name = f'{destination_file_name}_{file_number}'
    return destination_file_name


def determine_destination_file_name(
    *,
    source_full_path,
    destination_file_name,
        file_number=None):
    """
    Determine if the destination_file_name was provided, or should be extracted
    from the source_file_name, or should be enumerated for multiple file
    downloads.
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
    Cleans folders name by removing duplicate '/' as well as leading and
    trailing '/' characters.
    """
    folder_name = folder_name.strip('/')
    if folder_name != '':
        folder_name = os.path.normpath(folder_name)
    return folder_name


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path
    variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')
    combined_name = os.path.normpath(combined_name)

    return combined_name


def determine_destination_full_path(
        destination_folder_name,
        destination_file_name,
        source_full_path,
        file_number=None):
    """
    Determine the final destination name of the file being downloaded.
    """
    destination_file_name = determine_destination_file_name(
        destination_file_name=destination_file_name,
        source_full_path=source_full_path,
        file_number=file_number)
    destination_full_path = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)
    return destination_full_path


def find_all_local_file_names(source_folder_name):
    """
    Returns a list of all files that exist in the current working directory,
    filtered by source_folder_name if provided.
    """
    cwd = os.getcwd()
    cwd_extension = os.path.normpath(f'{cwd}/{source_folder_name}/*')
    file_names = glob.glob(cwd_extension)
    return file_names


def find_all_file_matches(file_names, file_name_re):
    """
    Return a list of all file_names that matched the regular expression.
    """
    matching_file_names = []
    for file in file_names:
        if re.search(file_name_re, file):
            matching_file_names.append(file)

    return matching_file_names


def upload_google_cloud_storage_file(
        gclient,
        bucket,
        source_full_path,
        destination_full_path):
    """
    Uploads a single file to Google Cloud Storage.
    """
    blob = bucket.blob(destination_full_path)
    blob.upload_from_filename(source_full_path)

    print(f'{source_full_path} successfully uploaded to ' \
            f'{bucket.name}/{destination_full_path}')


def get_gclient():
    """
    Attempts to create the Google Cloud Storage Client with the associated
    environment variables
    """
    try:
        gclient = storage.Client()
        return gclient
    except Exception as e:
        print(f'Error accessing Google Cloud Storage with service account ' \
                f'{args.gcp_application_credentials}')
        sys.exit(1)


def get_bucket(*,
        gclient,
        force_create,
        bucket_name):
    """
    Fetches and returns the bucket from Google Cloud Storage and creates it
    if force_create is set to True
    """
    if force_create:
        try:
            print(f'Creating bucket {bucket_name}')
            gclient.create_bucket(bucket_name)
        except Conflict as e:
            print(f'Bucket {bucket_name} already exists')

    try:
        bucket = gclient.get_bucket(bucket_name)
    except NotFound as e:
        print(f'Bucket {bucket_name} does not exist\n {e}')
        sys.exit(1)

    return bucket


def check_force_create(force_create):
    if not force_create:
        return False

    if force_create.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    else:
        return False


def main():
    args = get_args()
    set_environment_variables(args)
    bucket_name = args.bucket_name
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    source_full_path = combine_folder_and_file_name(
        folder_name=f'{os.getcwd()}/{source_folder_name}',
        file_name=source_file_name)
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    source_file_name_match_type = args.source_file_name_match_type
    force_create = check_force_create(args.force_create)

    gclient = get_gclient()
    bucket = get_bucket(gclient=gclient, force_create=force_create,
                    bucket_name=bucket_name)

    if source_file_name_match_type == 'regex_match':
        file_names = find_all_local_file_names(source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))
        print(f'{len(matching_file_names)} files found. Preparing to upload...')

        for index, key_name in enumerate(matching_file_names):
            destination_full_path = determine_destination_full_path(
                destination_folder_name=destination_folder_name,
                destination_file_name=args.destination_file_name,
                source_full_path=key_name,
                file_number=index + 1)
            print(f'Uploading file {index+1} of {len(matching_file_names)}')
            upload_google_cloud_storage_file(
                source_full_path=key_name,
                destination_full_path=destination_full_path,
                bucket=bucket,
                gclient=gclient)

    else:
        destination_full_path = determine_destination_full_path(
            destination_folder_name=destination_folder_name,
            destination_file_name=args.destination_file_name,
            source_full_path=source_full_path)
        upload_google_cloud_storage_file(
            source_full_path=source_full_path,
            destination_full_path=destination_full_path,
            bucket=bucket,
            gclient=gclient)


if __name__ == '__main__':
    main()
