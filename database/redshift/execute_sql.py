import argparse
import psycopg2


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument('--password', dest='password', required=False)
    parser.add_argument('--host', dest='host', required=True)
    parser.add_argument('--database',
                        dest='database', required=True)
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
    try:
        con = psycopg2.connect(dbname=database, host=host, port=port,
                            user=username, password=password)
    except Exception as e:
        print(f'Failed to connect to database {database}')
        raise(e)

    try:
        cur = con.cursor()
        cur.execute(query)
    except Exception as e:
        print(f'Failed to connect to database {database}')
        raise(e)

    print('Your query has been successfully executed.')


if __name__ == '__main__':
    main()
