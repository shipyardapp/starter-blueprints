# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

You will also need to create or use an existing Box App service account
that's generated My Apps section under Configuration, as well as client id.

Ref: https://account.box.com/developers/console
Ref(Service Account): https://www.magellanic-clouds.com/blocks/en/guide/create-box-service-accounts/

# Example Commands
## Upload

For this portion you can assume the **tests/** directory contains the files/subdirs
you wish to upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python cloud_storage/box/upload_file.py --source-folder-name FOLDER --source-file-name FILE_NAME --source-file-name-match-type (exact_match/regex_match) --destination-folder-name DESTINATION_FOLDER --destination-file-name DESTINATION_FILENAME --service-account SERVICE_ACCOUNT

This will upload the single file `test_file.txt` in the `tests` directory to the 
destination folder `box_folder`

venv/bin/python cloud_storage/box/upload_file.py --source-folder-name tests --source-file-name test_file.txt --source-file-name-match-type exact_match --destination-folder-name box_folder --destination-file-name exact_box_file.txt --service-account credentials.json

This will upload all files in the tests directory recursively that regex match
`test_file.txt` to the `box_folder` folder.
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python cloud_storage/box/upload_file.py --source-folder-name tests --source-file-name test_file.txt --source-file-name-match-type regex_match --destination-folder-name box_folder --destination-file-name box_file.txt --service-account credentials.json

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python cloud_storage/box/download_file.py --source-folder-name FOLDER --source-file-name FILE_NAME --source-file-name-match-type (exact_match/regex_match) --destination-folder-name DESTINATION_FOLDER --destination-file-name DESTINATION_FILENAME --service-account credentials.json

This will download the `test_file.txt` file to the local CWD

venv/bin/python cloud_storage/box/download_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --service-account credentials.json

This will download all files in the tests/ directory that regex match
`test_file.txt` to the local CWD
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python cloud_storage/box/download_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --service-account credentials.json

```

