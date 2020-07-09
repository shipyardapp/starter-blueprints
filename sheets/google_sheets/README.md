# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

You will need to enable the Google Sheets API. You will also need to create or
use an existing Google API Service Account which can be found here by 
creating a key for Google Drive API:

Refs: https://console.developers.google.com/apis/library, https://developers.google.com/sheets/api/quickstart/python

# Example Commands
## Upload

For this portion you can assume the **tests/** directory contains the files/subdirs
you wish to upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python sheets/google_sheets/upload_file.py --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --service-account "creds.json"

This will upload the contents of the csv `test_file.csv` in the `tests`
directory to a file call `Example Sheet` in Google Sheets.

venv/bin/python sheets/google_sheets/upload_file.py --source-file-name test_file.csv --source-folder-name tests/ --sheet-name "Example Sheet" --service-account "creds.json"

This will upload the csv contents of `test_file.csv` to the workbook `workbook1`
in the `Example Sheet` spreadsheet

venv/bin/python sheets/google_sheets/upload_file.py --source-file-name test_file.csv --source-folder-name tests/ --sheet-name "Example Sheet" --workbook-name 'workbook1' --service-account "creds.json"

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python sheets/google_sheets/download_file.py --sheet-name "download.csv" --workbook-name "ExampleSheet" --service-account "creds.json"

This will download the contents of the `test_file.csv` spreadsheet to a local
file from Google Sheets

venv/bin/python sheets/google_sheets/download_file.py --sheet-name "test_file.csv" --service-account "creds.json"

This will download the contents of sheet `Example Sheet` from the
`test_file.csv` spreadsheet to a local file from Google Sheets

venv/bin/python sheets/google_sheets/download_file.py --sheet-name "test_file.csv" --workbook-name "Example Sheet" --service-account "creds.json"

```

