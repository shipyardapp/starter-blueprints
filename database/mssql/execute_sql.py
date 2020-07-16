import argparse
import pymssql

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument('--password', dest='password', required=False)
    parser.add_argument('--host', dest='host', required=True)
    parser.add_argument('--database',
                        dest='database', required=False)
    parser.add_argument('--port', dest='port', default='5432', required=False)
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
    query = args.query

    db = pymssql.connect(server=host, user=username, password=password,
                        database=database, autocommit=True)
    cursor = db.cursor()

    cursor.execute(query)
    print('Your query has been successfully executed.')


if __name__ == '__main__':
    main()
