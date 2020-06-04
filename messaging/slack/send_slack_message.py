from slack import WebClient
import os
import time
import argparse
import code
import glob
import re
from zipfile import ZipFile


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--destination-type',
        dest='destination_type',
        required=True,
        choices={
            'channel',
            'dm'})
    parser.add_argument('--channel-name', dest='channel_name', required=False)
    parser.add_argument(
        '--user-lookup-method',
        dest='user_lookup_method',
        choices={
            'display_name',
            'real_name',
            'email'},
        required=False)
    parser.add_argument(
        '--users-to-notify',
        dest='users_to_notify',
        required=False)
    parser.add_argument('--message', dest='message', required=True)
    parser.add_argument(
        '--file-upload',
        dest='file_upload',
        required=True,
        choices={
            'yes',
            'no'})
    parser.add_argument(
        '--source-file-name-match-type',
        dest='source_file_name_match_type',
        choices={
            'exact_match',
            'regex_match'},
        required=False)
    parser.add_argument(
        '--source-file-name',
        dest='source_file_name',
        required=False)
    parser.add_argument(
        '--source-folder-name',
        dest='source_folder_name',
        default='',
        required=False)

    args = parser.parse_args()
    if args.destination_type == 'channel' and args.channel_name is None:
        parser.error('--destination-type channel requires --channel-name')
    elif args.destination_type == 'dm' and args.users_to_notify is None:
        parser.error('--destination-type dm requires --users-to-notify')

    if args.users_to_notify is not None and args.user_lookup_method is None:
        parser.error('--users-to-notify requires a --user-lookup-method')

    if args.file_upload == 'yes' and (
            args.source_file_name_match_type is None or args.source_file_name is None):
        parser.error(
            '--file-upload yes requires --source-file-name and --source-file-name-match-type')

    return args


def connect_to_slack():
    """
    Create a connection to Slack, using a "Bot User OAuth Access Token"
    stored under an environment variable of SLACK_TOKEN
    """
    slack_connection = WebClient(os.environ.get('SLACK_TOKEN'))
    return slack_connection


def send_slack_message(slack_connection, message, channel_name, blocks):
    """
    Send a slack message to the channel of your choice.
    Channel should be provided without a #
    Blocks will contain the main message, with text serving as a backup.
    """
    message_response = slack_connection.chat_postMessage(
        channel=channel_name, link_names=True, text=message, blocks=blocks)
    print(
        f'Your message of "{message}" was successfully sent to {channel_name}')
    return message_response


def upload_file_to_slack(slack_connection, file_name, channel_name, timestamp):
    """
    Upload a file to Slack in a thread under the main message.
    All channel members will have access to the file.
    Only works for files <50MB.
    """
    try:
        file_response = slack_connection.files_upload(
            file=file_name,
            filename=file_name,
            title=file_name,
            channels=channel_name,
            thread_ts=timestamp)
        print(f'{file_name} successfully uploaded.')
    except Exception as e:
        print(e)
        file_response = None
        print('File failed to upload.')
    return file_response


def get_message_details(message_response):
    """
    Return the channel_id and timestamp from the message_resposne. Used for updating the message
    or responding in a thread to the message.
    """
    channel_id = message_response['channel']
    timestamp = message_response['ts']
    return channel_id, timestamp


def slack_user_id_lookup(slack_connection, name_to_lookup, user_lookup_method):
    """
    Look up a user's Slack ID, using a provided search value and a lookup method.
    """
    tries = 3
    for attempt in range(tries):
        try:
            print('attempt ' + str(attempt + 1))
            users = slack_connection.users_list()
            user_id = ''
            for user in range(len(users['members'])):
                user_profile = users['members'][user]['profile']
                user_value = user_profile.get(user_lookup_method, '')

                if user_value.lower() == name_to_lookup.lower():
                    user_id = users['members'][user]['id']
                else:
                    pass

            if user_id == '':
                print('The name of "{}" does not exist in Slack.'.format(
                    name_to_lookup))

            return user_id
        except Exception as e:
            if attempt < tries - 1:  # i is zero indexed
                user_id = ''
                print('We werent able to connect to slack properly, trying again')
                print("")
                if attempt != tries - 1:
                    time.sleep(1)
            else:
                print("Couldn't connect to slack, error " + str(e))
                user_id = ''
                return user_id


def create_user_id_list(slack_connection, users_to_notify, user_lookup_method):
    """
    Create a list of all users to be notified.
    """
    users_to_notify = [x.strip() for x in users_to_notify.split(',')]

    user_id_list = []
    for user in users_to_notify:
        if user in ['@here', '@channel', '@everyone']:
            user_id_list.append(user.replace('@', ''))
        else:
            print('Looking up ' + user)
            user_id = slack_user_id_lookup(
                slack_connection, user, user_lookup_method)
            user_id_list.append(user_id)
    return user_id_list


def create_name_tags(user_id_list):
    """
    Create a string that consists of all the user_id tags
    that will be added at the beginning of a message.
    """
    names_to_prepend = ''

    for user_id in user_id_list:
        if user_id not in ['channel', 'here', 'everyone']:
            names_to_prepend += f'<@{user_id}> '
        else:
            names_to_prepend += f'<!{user_id}> '

    return names_to_prepend


def create_blocks(message, shipyard_link, download_link=''):
    """
    Create blocks for the main message, a divider, and context that links to Shipyard.
    If a download link is provided, creates a button block to immediately start that download.
    For more information: https://api.slack.com/block-kit/building
    """

    message_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": message,
            "verbatim": True
        }
    }
    divider_section = {
        "type": "divider"
    }
    context_section = {
        "type": "context",
        "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sent by Shipyard | <{shipyard_link}|Click Here to Edit>"
                }
        ]
    }

    if download_link != '':
        download_section = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Download File"
                    },
                    "value": "file_download",
                    "url": download_link,
                    "style": "primary"
                }
            ]
        }
        blocks = [message_section, download_section,
                  divider_section, context_section]
    else:
        blocks = [message_section, divider_section, context_section]

    return blocks


def create_shipyard_link():
    """
    Create a link back to the Shipyard log page for the current alert.
    """
    org_name = os.environ.get('SHIPYARD_ORG_NAME')
    project_id = os.environ.get('SHIPYARD_PROJECT_ID')
    vessel_id = os.environ.get('SHIPYARD_VESSEL_ID')
    log_id = os.environ.get('SHIPYARD_LOG_ID')

    if project_id and vessel_id and log_id:
        shipyard_link = f'https://app.shipyardapp.com/{org_name}/projects/{project_id}/vessels/{vessel_id}/logs/{log_id}'
    else:
        shipyard_link = 'https://www.shipyardapp.com'
    return shipyard_link


def get_file_download_details(file_response):
    """
    Return the download_link from the file_response.
    Used for updating the message with a download button.
    """
    download_link = file_response['file']['url_private_download']
    return download_link


def update_slack_message(
        slack_connection,
        message,
        channel_id,
        blocks,
        timestamp):
    response = slack_connection.chat_update(
        channel=channel_id,
        link_names=True,
        text=message,
        blocks=blocks,
        ts=timestamp)
    print(
        f'Your message was updated')
    return message


def find_all_local_file_names(source_folder_name):
    """
    Returns a list of all files that exist in the current working directory,
    filtered by source_folder_name if provided.
    """
    cwd = os.getcwd()
    cwd_extension = os.path.normpath(f'{cwd}/{source_folder_name}/**')
    file_names = glob.glob(cwd_extension, recursive=True)
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


def combine_folder_and_file_name(folder_name, file_name):
    """
    Combine together the provided folder_name and file_name into one path variable.
    """
    combined_name = os.path.normpath(
        f'{folder_name}{"/" if folder_name else ""}{file_name}')

    return combined_name


def compress_files(file_names):
    """
    Given a list of files, compress all of them into a single file.
    Keeps the existing directory structure in tact.
    """
    archive_file_name = 'archive.zip'
    print(f'{len(file_names)} files found. Compressing the files...')
    cwd = os.getcwd()
    with ZipFile(archive_file_name, 'w') as zip_file:
        for path in file_names:
            zip_file.write(path, path.replace(cwd, ''))
    print(
        f'All {len(file_names)} files were successfully compressed into {archive_file_name}')
    return archive_file_name


def is_too_large(file_path):
    """
    Determine if the file is too large for Slack's upload limit.
    Used to conditionally compress a file.
    """
    byte_max = 1000000000
    if os.stat(file_path).st_size >= byte_max:
        return True
    else:
        return False


def determine_file_to_upload(
        source_file_name_match_type,
        source_folder_name,
        source_file_name):
    """
    Determine whether the file name being uploaded to Slack
    will be named archive_file_name or will be the source_file_name provided.
    """
    if source_file_name_match_type == 'regex_match':
        file_names = find_all_local_file_names(source_folder_name)
        matching_file_names = find_all_file_matches(
            file_names, re.compile(source_file_name))

        file_to_upload = compress_files(matching_file_names)
    else:
        source_full_path = combine_folder_and_file_name(
            folder_name=source_folder_name, file_name=source_file_name)
        if is_too_large(source_full_path):
            print(f'{source_full_path} is too large. Compressing the file...')
            file_to_upload = compress_files([source_full_path])
        else:
            file_to_upload = source_full_path
    return file_to_upload


def send_slack_message_with_file(
        slack_connection,
        message,
        channel,
        shipyard_link,
        file_to_upload):
    """
    Sends an initial Slack message with the file upload status in progress.
    Attempts to upload the file. If successful, updates the first message with a download button.
    If unsuccessful, updates the message to let users know.
    """
    message_with_file_status = message + \
        '\n\n _(File is currently uploading...)_'
    message_response = send_slack_message(
        slack_connection,
        message_with_file_status,
        channel,
        create_blocks(
            message_with_file_status,
            shipyard_link))
    channel_id, timestamp = get_message_details(message_response)
    file_response = upload_file_to_slack(
        slack_connection,
        file_name=file_to_upload,
        channel_name=channel,
        timestamp=timestamp)
    if file_response:
        download_link = get_file_download_details(file_response)
        update_slack_message(
            slack_connection,
            message,
            channel_id=channel_id,
            blocks=create_blocks(
                message,
                download_link=download_link,
                shipyard_link=shipyard_link),
            timestamp=timestamp)
    else:
        message_with_file_status = message + \
            '\n\n _(File could not be uploaded. Check log for details)_'
        update_slack_message(
            slack_connection,
            message,
            channel_id=channel_id,
            blocks=create_blocks(
                message_with_file_status,
                shipyard_link=shipyard_link),
            timestamp=timestamp)


def main():
    args = get_args()
    destination_type = args.destination_type
    channel_name = args.channel_name
    message = args.message
    user_lookup_method = args.user_lookup_method
    users_to_notify = args.users_to_notify.lower()
    file_upload = args.file_upload
    source_file_name = args.source_file_name
    source_folder_name = args.source_folder_name
    source_file_name_match_type = args.source_file_name_match_type

    shipyard_link = create_shipyard_link()
    slack_connection = connect_to_slack()
    user_id_list = create_user_id_list(
        slack_connection, users_to_notify, user_lookup_method)

    if destination_type == 'dm':
        for user_id in user_id_list:

            if file_upload == 'yes':
                file_to_upload = determine_file_to_upload(
                    source_file_name_match_type, source_folder_name, source_file_name)
                send_slack_message_with_file(
                    slack_connection, message, user_id, shipyard_link, file_to_upload)
            else:
                send_slack_message(
                    slack_connection,
                    message,
                    user_id,
                    create_blocks(
                        message,
                        shipyard_link))

    else:
        names_to_tag = create_name_tags(user_id_list)
        message = names_to_tag + message

        if file_upload == 'yes':
            file_to_upload = determine_file_to_upload(
                source_file_name_match_type, source_folder_name, source_file_name)
            send_slack_message_with_file(
                slack_connection,
                message,
                channel_name,
                shipyard_link,
                file_to_upload)
        else:
            message_response = send_slack_message(
                slack_connection, message, channel_name, create_blocks(
                    message, shipyard_link))


if __name__ == '__main__':
    main()
