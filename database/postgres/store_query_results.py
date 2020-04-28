from sqlalchemy import create_engine, text
import argparse
import code
import pandas as pd


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument('--password', dest='password', required=True)
    parser.add_argument('--host', dest='host', required=True)
    parser.add_argument('--database',
                        dest='database', required=True)
    parser.add_argument('--port', dest='port', default='5432', required=False)
    parser.add_argument('--url-parameters',
                        dest='url_parameters', required=False)
    parser.add_argument('--query', dest='query', required=True)
    args = parser.parse_args()
    return args


def create_csv(query, db_connection, destination_file_path):
    df = pd.read_sql_query(query, db_connection)
    df.to_csv(destination_file_path)
    return


def main():
    args = get_args()
    username = args.username
    password = args.password
    host = args.host
    database = args.database
    port = args.port
    url_parameters = args.url_parameters
    query = text(args.query)

    db_string = f'postgresql://{username}:{password}@{host}:{port}/{database}?{url_parameters}'
    db = create_engine(db_string)

    create_csv(query, db, 'output.csv')


if __name__ == '__main__':
    main()
