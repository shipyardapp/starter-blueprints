import time
import argparse

import boto3


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--access-key', dest='access_key', required=True)
    parser.add_argument('--secret-key', dest='secret_key', required=False)
    parser.add_argument('--region-name', dest='region_name', required=True)
    parser.add_argument('--bucket', dest='bucket', required=True)
    parser.add_argument('--database', dest='database', required=True)
    parser.add_argument('--query', dest='query', required=True)
    args = parser.parse_args()
    return args


def poll_status(client, job_id):
    '''
    poll query status
    '''
    result = client.get_query_execution(
        QueryExecutionId = job_id
    )

    state = result['QueryExecution']['Status']['State']
    if state == 'SUCCEEDED':
        print(f'Query completed')
        return result
    elif state == 'FAILED':
        error_msg = result['QueryExecution']['Status'].get('StateChangeReason')
        print(f'Query failed')
        print(error_msg)
        return result
    return False


def main():
    args = get_args()
    access_key = args.access_key
    secret_key = args.secret_key
    region_name = args.region_name
    database = args.database
    bucket = args.bucket
    query = args.query

    try:
        client = boto3.client('athena', region_name=region_name,
                aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    except Exception as e:
        print(f'Failed to access Athena with specified credentials')
        raise(e)

    job = client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database},
                ResultConfiguration={'OutputLocation': f's3://{bucket}/'}
                )

    job_id = job['QueryExecutionId']

    status = poll_status(client, job_id)
    while not status:
        time.sleep(0.1)
        status = poll_status(client, job_id)

    if status['QueryExecution']['Status']['State'] != 'FAILED':
        print('Your query has been successfully executed.')


if __name__ == '__main__':
    main()
