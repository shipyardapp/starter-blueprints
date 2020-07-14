# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

# Example Commands
## Upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/snowflake/execute_sql.py --query 'QUERY' --username USERNAME --password PASSWORD --account ACCOUNT --password PASSWORD --database DB_NAME


This will execute the INSERT command to the table under the dataset.

venv/bin/python database/snowflake/execute_sql.py --query 'INSERT dataset.table_name ...' --username USERNAME --password PASSWORD --account ACCOUNT --password PASSWORD --database dataset

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/snowflake/store_query_results.py --query 'QUERY' --username USERNAME --password PASSWORD --account ACCOUNT --database DB_NAME --destination-file-name DESTINATION_FILE_NAME

This will execute the SELECT command on table_name under the dataset and store it
as a csv to 'output.csv'

venv/bin/python database/snowflake/store_query_results.py --query 'INSERT dataset.table_name ...' --username USERNAME --password PASSWORD --account ACCOUNT --database DB_NAME --destination-file-name output.csv
```
