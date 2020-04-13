from slack import WebClient
import os
import time
import argparse


def getArgs(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel_type', dest='channel_type', required=True,
                        choices={'public', 'private', 'dm'})
    parser.add_argument('--channel', dest='channel')
    parser.add_argument('--user_lookup_method', dest='user_lookup_method',
                        choices={'display_name', 'real_name', 'email'})
    parser.add_argument('--users_to_notify', dest='users_to_notify')
    parser.add_argument('--message', dest='message')
    parser.add_argument('--is_visible', dest='is_visible',
                        default='True', required=True)
    return parser.parse_args()


def connect_to_slack(slack_token):
    slack_connection = WebClient(os.environ.get(slack_token))
    return slack_connection


def send_slack_message(slack_connection, message, channel):
    slack_connection.chat_postMessage(
        channel=channel, link_names=True, text=message)
    print(
        f'Your public message of "{message}" was successfully sent to {channel}')


def send_private_slack_message(slack_connection, message, channel, user):
    slack_connection.chat_postEphemeral(
        channel=channel, link_names=True, text=message, user=user)
    print(
        f'Your private message of "{message}" was successfully sent to {channel}')


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


args = getArgs()
channel_type = args.channel_type
channel = args.channel
message = args.message
user_lookup_method = args.user_lookup_method
users_to_notify = args.users_to_notify.lower()
is_visible = args.is_visible.lower()


slack_connection = connect_to_slack('SHIPYARD_SLACK_TOKEN')
user_id_list = create_user_id_list(users_to_notify)

if channel_type == 'dm':
    channel = user_id_list[0]

print(f'Sending to {channel}...')

if channel_type == 'dm':
    for user_id in user_id_list:
        print(user_id)
        send_slack_message(slack_connection, message, user_id)
else:
    if is_visible in ('true', 'y', 'yes'):
        names_to_tag = create_name_tags(user_id_list)
        message = names_to_tag + message
        send_slack_message(slack_connection, message, channel)
    else:
        for user_id in user_id_list:
            message = create_name_tags([user_id]) + message
            send_private_slack_message(
                slack_connection, message, channel, user_id)
