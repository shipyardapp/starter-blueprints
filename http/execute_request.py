import argparse
import requests


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--method', dest='method', required=True,
            choices={'GET', 'POST', 'PUT'})
    parser.add_argument('--url', dest='url', required=True)
    parser.add_argument('--authorization-header', dest='authorization_header',
            required=False, default={})
    parser.add_argument('--message', dest='message', required=False)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    method = args.method
    url = args.url
    authorization_header = args.authorization_header
    message = args.message

    try:
        if method == 'GET':
            req = requests.get(url, headers=authorization_header)
        elif method == 'POST':
            req = requests.post(url, headers=authorization_header, data=message)
        elif method == 'PUT':
            req = requests.put(url, headers=authorization_header, data=message)
    except Exception as e:
        print(f'Failed to execute {method} request to {url}')
        raise(e)

    print(f'Successfully sent request {url}. Response body: {req.content}')


if __name__ == '__main__':
    main()

