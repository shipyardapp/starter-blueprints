import argparse
import json
import requests


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--method', dest='method', required=True,
            choices={'GET', 'POST', 'PUT'})
    parser.add_argument('--url', dest='url', required=True)
    parser.add_argument('--authorization-key', dest='authorization_key',
            required=False)
    parser.add_argument('--authorization-value', dest='authorization_value',
            required=False)
    parser.add_argument('--message', dest='message', required=False)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    method = args.method
    url = args.url
    authorization_key = args.authorization_key
    authorization_value = args.authorization_value
    message = args.message

    auth_headers = {}
    if authorization_key and authorization_value:
        auth = f'{authorization_key}:{authorization_value}'
        auth_headers = {'Authorization': auth}

    try:
        if method == 'GET':
            req = requests.get(url, headers=auth_headers)
        elif method == 'POST':
            req = requests.post(url, headers=auth_headers, data=message)
        elif method == 'PUT':
            params = json.loads(message)
            req = requests.put(url, headers=auth_headers, data=params)
    except Exception as e:
        print(f'Failed to execute {method} request to {url}')
        raise(e)

    print(f'Successfully sent request {url}')


if __name__ == '__main__':
    main()

