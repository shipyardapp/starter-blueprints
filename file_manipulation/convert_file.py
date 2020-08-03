import glob
import os
import re
import argparse
import pandas as pd
import ast
import code


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--source-file-name-match-type',
        dest='source_file_name_match_type',
        default='exact_match',
        choices={
            'exact_match',
            'regex_match'},
        required=False)
    parser.add_argument(
        '--source-file-name',
        dest='source_file_name',
        required=True)
    parser.add_argument(
        '--source-folder-name',
        dest='source_folder_name',
        default='',
        required=False)
    parser.add_argument(
        '--destination-folder-name',
        dest='destination_folder_name',
        default='',
        required=False)
    parser.add_argument(
        '--destination-file-name',
        dest='destination_file_name',
        default=None,
        required=False)
    parser.add_argument(
        '--destination-file-format',
        dest='destination_file_format',
        choices={
            'tsv',
            'psv',
            'xlsx',
            'parquet',
            'stata',
            'hdf5'},
        required=True)
    parser.add_argument('--extra-args', dest='extra_args', default='{}')
    return parser.parse_args()


def extract_file_name_from_source_full_path(source_full_path):
    """
    Use the file name provided in the source_full_path variable. Should be run only
    if a destination_file_name is not provided.
    """
    destination_file_name = os.path.basename(source_full_path)
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


def create_fallback_destination_file_name(
        source_file_name, destination_file_format):
    """
    If a destination_file_name is not provided, uses the source_file_name with a removal of the compression extension.
    """

    format_extensions = {
        "tsv": ".tsv",
        "psv": ".psv",
        "xlsx": ".xlsx",
        "parquet": ".parquet",
        "stata": ".dta",
        "hdf5": ".h5"
    }

    file_name = os.path.basename(source_file_name)
    file_name = f'{os.path.splitext(file_name)[0]}{format_extensions[destination_file_format]}'
    return file_name


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
    source_full_path,
    destination_file_name,
    destination_file_format,
    file_number=None,
):
    """
    Determine if the destination_file_name was provided, or should be extracted
    from the source_file_name, or should be enumerated for multiple file
    uploads.
    """
    if destination_file_name:
        if file_number:
            destination_file_name = enumerate_destination_file_name(
                destination_file_name, file_number)
        else:
            destination_file_name = destination_file_name
    else:
        destination_file_name = create_fallback_destination_file_name(
            source_full_path, destination_file_format)

    return destination_file_name


def determine_destination_full_path(
        destination_folder_name,
        destination_file_name,
        source_full_path,
        destination_file_format,
        file_number=None,
):
    """
    Determine the final destination name of the file being uploaded.
    """
    destination_file_name = determine_destination_file_name(
        destination_file_name=destination_file_name,
        source_full_path=source_full_path,
        destination_file_format=destination_file_format,
        file_number=file_number)
    destination_full_path = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)
    return destination_full_path


def convert_file(
        source_full_path,
        destination_file_format,
        destination_full_path,
        **extra_args):
    input_df = pd.read_csv(source_full_path)

    if destination_file_format in ['tsv', 'psv']:
        if 'chunksize' not in extra_args:
            extra_args['chunksize'] = 10000
        if 'index' not in extra_args:
            extra_args['index'] = False
        if destination_file_format == 'tsv':
            input_df.to_csv(destination_full_path, sep='\t', **extra_args)
        if destination_file_format == 'psv':
            input_df.to_csv(destination_full_path, sep='|', **extra_args)
    if destination_file_format == 'xlsx':
        if 'index' not in extra_args:
            extra_args['index'] = False
        # Currently always shows the user an error message that their file
        # needs to be repaired, but I couldn't visibily see issues.
        input_df.to_excel(destination_full_path,
                          engine='xlsxwriter', **extra_args)
    if destination_file_format == 'parquet':
        input_df.to_parquet(destination_full_path, **extra_args)
    if destination_file_format == 'stata':
        input_df.to_stata(destination_full_path, **extra_args)
    if destination_file_format == 'hdf5':
        input_df.to_hdf(destination_full_path, key='shipyard', **extra_args)

    print(
        f'Successfully converted {source_full_path} to {destination_full_path}')
    return


def main():
    args = get_args()

    source_file_name = args.source_file_name
    source_folder_name = clean_folder_name(args.source_folder_name)
    source_full_path = combine_folder_and_file_name(
        folder_name=source_folder_name, file_name=source_file_name)
    source_file_name_match_type = args.source_file_name_match_type
    destination_folder_name = clean_folder_name(args.destination_folder_name)
    destination_file_name = args.destination_file_name
    destination_file_format = args.destination_file_format
    if destination_file_name is None:
        destination_file_name = create_fallback_destination_file_name(
            source_file_name, destination_file_format)
    destination_full_path = combine_folder_and_file_name(
        destination_folder_name, destination_file_name)
    extra_args = ast.literal_eval(args.extra_args)

    if not os.path.exists(destination_folder_name) and (
            destination_folder_name != ''):
        os.makedirs(destination_folder_name)

    if source_file_name_match_type == 'regex_match':
        file_names = find_all_local_file_names(source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))
        if len(matching_file_names) > 0:
            print(f'{len(matching_file_names)} files found. Preparing to convert...')

            for index, key_name in enumerate(matching_file_names):
                destination_full_path = determine_destination_full_path(
                    destination_folder_name=destination_folder_name,
                    destination_file_name=args.destination_file_name,
                    source_full_path=key_name,
                    file_number=index + 1,
                    destination_file_format=destination_file_format)
                print(
                    f'Converting file {index+1} of {len(matching_file_names)} to {destination_file_format}')
                try:
                    convert_file(
                        source_full_path=key_name,
                        destination_file_format=destination_file_format,
                        destination_full_path=destination_full_path,
                        **extra_args)
                except Exception as e:
                    print(f'Could not convert {source_full_path}')
                    print(e)
        else:
            print('No matches were found.')

    else:
        destination_full_path = determine_destination_full_path(
            destination_folder_name=destination_folder_name,
            destination_file_name=args.destination_file_name,
            source_full_path=source_full_path,
            destination_file_format=destination_file_format)
        try:
            convert_file(
                source_full_path=source_full_path,
                destination_file_format=destination_file_format,
                destination_full_path=destination_full_path,
                **extra_args)
        except Exception as e:
            print(f'Could not convert {source_full_path}')
            print(e)


if __name__ == '__main__':
    main()
