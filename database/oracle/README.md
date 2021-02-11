# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

NOTE: You will need to install Oracle Client Libraries and export the LD_LIBRARY_PATH
      accordingly. Nice tutorial: https://sujanbyanjankar.com.np/oracle-instant-client-in-ubuntu/
      Client downloads: https://www.oracle.com/database/technologies/instant-client/downloads.html

      After installation you will need to:
        `export LD_LIBRARY_PATH=/opt/oracle/instantclient:$LD_LIBRARY_PATH`

# Example Commands
## Upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/oracle/execute_sql.py --query 'QUERY' ---host HOST -username USERNAME --password PASSWORD --port PORT --password PASSWORD --database DB_NAME


This will execute the INSERT command to the table under the database.

venv/bin/python database/oracle/execute_sql.py --query 'INSERT table_name ...' ---host HOST -username USERNAME --password PASSWORD --port PORT --password PASSWORD --database database

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python database/oracle/store_query_results.py --query 'QUERY' ---host HOST -username USERNAME --password PASSWORD --port PORT --database DB_NAME --destination-file-name DESTINATION_FILE_NAME

This will execute the SELECT command on table_name under the database and store it
as a csv to 'output.csv'

venv/bin/python database/oracle/store_query_results.py --query 'INSERT table_name ...' ---host HOST -username USERNAME --password PASSWORD --port PORT --database DB_NAME --destination-file-name output.csv
```
