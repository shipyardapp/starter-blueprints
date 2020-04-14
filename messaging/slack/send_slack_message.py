from slack import WebClient
import os
import time
import argparse
import code


def getArgs(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination-type', dest='destination_type', required=True,
                        choices={'channel', 'dm'})
    parser.add_argument('--channel-name', dest='channel_name', required=False)
    parser.add_argument('--user-lookup-method', dest='user_lookup_method',
                        choices={'display_name', 'real_name', 'email'}, required=False)
    parser.add_argument('--users-to-notify',
                        dest='users_to_notify', required=False)
    parser.add_argument('--message', dest='message', required=True)
    parser.add_argument('--source-file-name', dest='source_file_name',
                        required=False)
    parser.add_argument('--source-folder-name', dest='source_folder_name',
                        default='', required=False)
    return parser.parse_args()


def connect_to_slack():
    slack_connection = WebClient(os.environ.get('SHIPYARD_SLACK_TOKEN'))
    return slack_connection


def send_slack_message(slack_connection, message, channel_name, blocks):
    message_response = slack_connection.chat_postMessage(
        channel=channel_name, link_names=True, text=message, blocks=blocks)
    print(
        f'Your message of "{message}" was successfully sent to {channel_name}')
    return response


def upload_file_to_slack(slack_connection, file_name, channel_name, timestamp):
    file_response = slack_connection.files_upload(
        file=file_name, filename=file_name, title=file_name, channels=channel_name, thread_ts=timestamp)
    return file_response


def get_message_details(message_response):
    channel_id = message_response['channel']
    timestamp = message_response['ts']
    return channel_id, timestamp


def slack_user_id_lookup(slack_connection, name_to_lookup, user_lookup_method='display_name'):
    tries = 3
    for attempt in range(tries):
        try:
            print('attempt ' + str(attempt+1))
            users = slack_connection.users_list()
            user_id = ''
            for user in range(len(users['members'])):
                user_profile = users['members'][user]['profile']
                user_value = user_profile.get(user_lookup_method, '').lower()

                if user_value == name_to_lookup:
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
                if attempt != 2:
                    time.sleep(1)
            else:
                print("Couldn't connect to slack, error " + str(e))
                user_id = ''
                return user_id


def create_user_id_list(users_to_notify):
    users_to_notify = users_to_notify.replace(
        ', ', ',').replace(' ,', ',').split(',')
    if type(users_to_notify) is str:
        users_to_notify = [users_to_notify]

    user_id_list = []
    for user in users_to_notify:
        if user == '@here':
            user_id_list.append('@here ')
        elif user == '@channel':
            user_id_list.append('@channel ')
        else:
            print('Looking up ' + user)
            user_id = slack_user_id_lookup(
                slack_connection, user, user_lookup_method)
            user_id_list.append(user_id)
    return user_id_list


def create_name_tags(user_id_list):
    names_to_prepend = ''

    for user_id in user_id_list:
        names_to_prepend += ('<@' + user_id + '> ')

    return names_to_prepend


def create_blocks(message, shipyard_link, download_link=''):

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


def create_shipyard_link(project_id, vessel_id, log_id):
    if project_id and vessel_id and log_id:
        shipyard_link = f'https://app.shipyardapp.com/Shipyard/projects/{project_id}/vessels/{vessel_id}/logs/{log_id}'
    else:
        shipyard_link = 'https://www.shipyardapp.com'
    return shipyard_link


def get_file_download_details(file_response):
    timestamp = file_response['file']['timestamp']
    download_link = file_response['file']['url_private_download']
    return timestamp, download_link


def update_slack_message(slack_connection, message, channel_id, blocks, timestamp):
    response = slack_connection.chat_update(
        channel=channel_id, link_names=True, text=message, blocks=blocks, ts=timestamp)
    print(
        f'Your message was updated')
    return message


args = getArgs()
destination_type = args.destination_type
channel_name = args.channel_name
message = args.message
user_lookup_method = args.user_lookup_method
users_to_notify = args.users_to_notify.lower()
source_file_name = args.source_file_name
source_folder_name = args.source_folder_name


project_id = os.environ.get('SHIPYARD_PROJECT_ID')
vessel_id = os.environ.get('SHIPYARD_VESSEL_ID')
log_id = os.environ.get('SHIPYARD_LOG_ID')

shipyard_link = create_shipyard_link(
    project_id=project_id, vessel_id=vessel_id, log_id=log_id)

slack_connection = connect_to_slack()
user_id_list = create_user_id_list(users_to_notify)


if destination_type == 'dm':
    for user_id in user_id_list:
        message_response = send_slack_message(
            slack_connection, message, user_id, create_blocks(message, shipyard_link))
        if source_file_name:
            channel_id, timestamp = get_message_details(message_response)
            file_response = upload_file_to_slack(
                slack_connection, file_name=source_file_name, channel=user_id, timestamp=timestamp)

else:
    names_to_tag = create_name_tags(user_id_list)
    message = names_to_tag + message
    create_blocks(message, shipyard_link)
    message_response = send_slack_message(
        slack_connection, message, channel_name, create_blocks(message, shipyard_link))
    if source_file_name:
        channel_id, timestamp = get_message_details(message_response)
        file_response = upload_file_to_slack(
            slack_connection, file_name=source_file_name, channel=channel_name, timestamp=timestamp)


file_timestamp, download_link = get_file_download_details(file_response)
update_slack_message(slack_connection, message, channel=channel_id, blocks=create_blocks(
    message, download_link=download_link, shipyard_link=shipyard_link), timestamp=timestamp)


# code.interact(local=locals())
