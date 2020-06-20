import argparse
import os
from zipfile import ZipFile
import tarfile
import glob
import re

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compression', dest='compression',
                        choices={'zip','tar','tar.bz2','tar.gz'}, required=True)
    parser.add_argument('--source-folder-name',
                        dest='source_folder_name', default='', required=False)
    parser.add_argument('--source-file-name',
                        dest='source_file_name', required=True)
    parser.add_argument('--destination-file-name',
                        dest='destination_file_name', required=False)
    parser.add_argument('--destination-folder-name',
                        dest='destination_folder_name', default='', required=False)
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

def decompress_file(source_full_path,destination_full_path,compression):
    
    compressed_file_name = f'{destination_full_path}.{compression}'
    if compression == 'zip':
        with ZipFile(source_full_path, 'r') as zip:
            zip.extractall(destination_full_path)
                
    if compression =='tar.bz2':
        tf = tarfile.open(source_full_path,'r:bz2')
        tf.extractall(path=destination_full_path)

    if compression =='tar':
        tf = tarfile.open(source_full_path,'r')
        tf.extractall(path=destination_full_path)

    if compression =='tar.gz':
        tf = tarfile.open(source_full_path,'r:gz')
        tf.extractall(path=destination_full_path)

def create_fallback_destination_file_name(source_file_name,compression):
    file_name = os.path.basename(source_file_name)
    file_name = file_name.replace(f'.{compression}','')
    return file_name

def main():
    args = get_args()
    compression = args.compression
    source_file_name = args.source_file_name
    source_folder_name = clean_folder_name(args.source_folder_name)
    source_full_path = combine_folder_and_file_name(
        folder_name=source_folder_name, file_name=source_file_name)
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    destination_file_name = args.destination_file_name

    if destination_file_name is None:
        destination_file_name = create_fallback_destination_file_name(source_file_name,compression)

    destination_full_path = combine_folder_and_file_name(destination_folder_name, destination_file_name)

    if not os.path.exists(destination_folder_name) and (destination_folder_name != ''):
        os.makedirs(destination_folder_name)
    decompress_file(source_full_path,destination_full_path,compression)


if __name__ == '__main__':
    main()