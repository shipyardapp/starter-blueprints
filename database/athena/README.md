# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

NOTE: VPC routes and security network routing must be setup according to:
      https://docs.aws.amazon.com/athena/latest/mgmt/connecting-refusal-failure-issues.html
      Also `Publicly accessible` needs to be enabled on the athena Cluster

# Example Commands
## Upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/athena/execute_sql.py --query 'QUERY' --access-key ACCESS-KEY --secret-key SECRET-KEY --bucket bucket --region-name REGION-NAME --database DB_NAME --destination-file-name storage.csv


This will execute the INSERT command to the table under the database.

venv/bin/python database/athena/execute_sql.py --access-key ACCESSKEYXXXXXXXXXXX --secret-key SECRETKEYXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX --region-name us-west-2 --bucket BUCKET-XXX/ --database DB_NAME --query 'INSERT ....'
```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/athena/store_query_results.py --query 'QUERY' --access-key ACCESS-KEY --secret-key SECRET-KEY --bucket bucket --region-name REGION-NAME --database DB_NAME --destination-file-name DESTINATION_FILE_NAME

This will execute the SELECT command on table_name under the database and store it
as a csv to 'output.csv'

venv/bin/python database/athena/store_query_results.py --access-key ACCESSKEYXXXXXXXXXXX --secret-key SECRETKEYXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX --region-name us-west-2 --bucket BUCKET-XXX/ --database DB_NAME --query 'SELECT * FROM ....' --destination-file-name output.csv
```
