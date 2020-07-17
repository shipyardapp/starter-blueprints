from sqlalchemy import create_engine, text
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument('--password', dest='password', required=False)
    parser.add_argument('--host', dest='host', required=True)
    parser.add_argument('--database', dest='database', required=True)
    parser.add_argument('--port', dest='port', default='3306', required=False)
    parser.add_argument('--url-parameters',
                        dest='url_parameters', required=False)
    parser.add_argument('--query', dest='query', required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    username = args.username
    password = args.password
    host = args.host
    database = args.database
    port = args.port
    url_parameters = args.url_parameters
    query = text(args.query)

    db_string = f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}?{url_parameters}'
    db = create_engine(db_string, pool_recycle=3600, execution_options=dict(
        stream_results=True))

    db.execute(query)
    print('Your query has been successfully executed.')


if __name__ == '__main__':
    main()
