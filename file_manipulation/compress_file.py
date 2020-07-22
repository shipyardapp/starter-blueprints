import argparse
import os
from zipfile import ZipFile
import tarfile
import glob
import re


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--compression',
        dest='compression',
        choices={
            'zip',
            'tar',
            'tar.bz2',
            'tar.gz'},
        required=True)
    parser.add_argument(
        '--source-file-name-match-type',
        dest='source_file_name_match_type',
        choices={
            'exact_match',
            'regex_match'},
        required=True)
    parser.add_argument('--source-folder-name',
                        dest='source_folder_name', default='', required=False)
    parser.add_argument('--source-file-name',
                        dest='source_file_name', required=True)
    parser.add_argument(
        '--destination-file-name',
        dest='destination_file_name',
        default='Archive',
        required=False)
    parser.add_argument(
        '--destination-folder-name',
        dest='destination_folder_name',
        default='',
        required=False)
    return parser.parse_args()


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
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')
    combined_name = os.path.normpath(combined_name)

    return combined_name


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


def compress_files(file_paths, destination_full_path, compression):
    """
    Compress all of the matched files using the specified compression method.
    """
    compressed_file_name = f'{destination_full_path}.{compression}'
    if compression == 'zip':
        with ZipFile(compressed_file_name, 'w') as zip:
            for file in file_paths:
                file = file.replace(os.getcwd(), '')[1:]
                zip.write(file)

    if compression == 'tar.bz2':
        with tarfile.open(compressed_file_name, 'w:bz2') as tar:
            for file in file_paths:
                file = file.replace(os.getcwd(), '')[1:]
                tar.add(file)

    if compression == 'tar':
        with tarfile.open(compressed_file_name, 'w') as tar:
            for file in file_paths:
                file = file.replace(os.getcwd(), '')[1:]
                tar.add(file)

    if compression == 'tar.gz':
        with tarfile.open(compressed_file_name, 'w:gz') as tar:
            for file in file_paths:
                file = file.replace(os.getcwd(), '')[1:]
                tar.add(file)


def main():
    args = get_args()
    compression = args.compression
    source_file_name = args.source_file_name
    source_folder_name = clean_folder_name(args.source_folder_name)
    source_full_path = combine_folder_and_file_name(
        folder_name=source_folder_name, file_name=source_file_name)
    source_file_name_match_type = args.source_file_name_match_type
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    destination_file_name = args.destination_file_name
    destination_full_path = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)

    if source_file_name_match_type == 'regex_match':
        file_paths = find_all_local_file_names(source_folder_name)
        matching_file_paths = find_all_file_matches(
            file_paths, re.compile(source_file_name))
        print(
            f'{len(matching_file_paths)} files found. Preparing to compress with {compression}...')
        if not os.path.exists(destination_folder_name) and (
                destination_folder_name != ''):
            os.makedirs(destination_folder_name)
        compress_files(matching_file_paths, destination_full_path, compression)
    else:
        if not os.path.exists(destination_folder_name) and (
                destination_folder_name != ''):
            os.makedirs(destination_folder_name)
        compress_files([source_full_path], destination_full_path, compression)


if __name__ == '__main__':
    main()
