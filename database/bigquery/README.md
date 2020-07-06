# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

You will also need to create or use an existing Google API Service Account
which can be found here by creating a key for Google Big Query:

NOTE: The service account used must contain the `Cloud Datastore Owner` role

https://console.developers.google.com/apis/library

# Example Commands
## Upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/bigquery/execute_sql.py --query 'QUERY' --service-account 'SERVICE_ACCOUNT'

This will execute the INSERT command to the table under the dataset.

venv/bin/python database/bigquery/execute_sql.py --query 'INSERT dataset.table_name ...' --service-account 'SERVICE_ACCOUNT.json'

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/bigquery/execute_sql.py --query 'QUERY' --service-account 'SERVICE_ACCOUNT' --destination-file-name 'FILE_NAME' --destination-folder-name 'FOLDER_NAME'

This will execute the SELECT command on table_name under the dataset and store it
as a csv to 'output.csv'

venv/bin/python database/bigquery/execute_sql.py --query 'INSERT dataset.table_name ...' --service-account 'SERVICE_ACCOUNT.json' --destination-file-name 'output.csv'

```
