# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

NOTE: VPC routes and security network routing must be setup according to:
      https://docs.aws.amazon.com/redshift/latest/mgmt/connecting-refusal-failure-issues.html
      Also `Publicly accessible` needs to be enabled on the Redshift Cluster

# Example Commands
## Upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/redshift/execute_sql.py --query 'QUERY' --host HOST --port PORT --username USERNAME --password PASSWORD --database DB_NAME --destination-file-name storage.csv


This will execute the INSERT command to the table under the dataset.

venv/bin/python database/redshift/execute_sql.py --query 'INSERT dataset.table_name ...' --service-account 'SERVICE_ACCOUNT.json'

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/redshift/execute_sql.py --query 'QUERY' --host HOST --port PORT --username USERNAME --password PASSWORD --database DB_NAME --destination-file-name DESTINATION_FILE_NAME

This will execute the SELECT command on table_name under the dataset and store it
as a csv to 'output.csv'

venv/bin/python database/redshift/execute_sql.py --query 'INSERT dataset.table_name ...' --host HOST --port PORT --username USERNAME --password PASSWORD --database DB_NAME --destination-file-name output.csv
```
