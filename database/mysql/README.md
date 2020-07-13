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

venv/bin/python database/mysql/execute_sql.py --query 'QUERY' --host HOST --port PORT --username USERNAME --password PASSWORD --database DB_NAME


This will execute the INSERT command to the TABLEXYZ under MyDataBase.

venv/bin/python database/mysql/execute_sql.py --host "mysql.host" --username "USERXXX" --password "PASSXXXX" --query 'INSERT TABLEXYZ ...' --database "MyDataBase"

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/mysql/store_query_results.py --query 'QUERY' --host HOST --port PORT --username USERNAME --password PASSWORD --database DB_NAME --destination-file-name DESTINATION_FILE_NAME

This will execute the SELECT command on table_name under the database and store it
as a csv to 'output.csv'

venv/bin/python database/mysql/store_query_results.py --query 'INSERT table_name ...' --host HOST --port PORT --username USERNAME --password PASSWORD --database DB_NAME --destination-file-name output.csv
```
