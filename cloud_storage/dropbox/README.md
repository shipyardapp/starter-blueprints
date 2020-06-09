# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```


You will also need to have a Dropbox account and create an app which will allow
you to generate an access token.

More info: https://www.dropbox.com/developers/apps/create

# Example Commands
## Upload

For this portion you can assume the **tests/** directory contains the files/subdirs
you wish to upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python cloud_storage/dropbox/upload_file.py --source-file-name-match-type (exact_match/regex_match) --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --access-key 'ACCESS-KEY'

This will upload the single file `test_file.txt` in the `tests` directory to the 
root dropbox folder

venv/bin/python cloud_storage/dropbox/upload_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --access-key 'fT87blahTblahAAAAAAAblahO54nviTug-n7CblblahpMB6kblahvIqWfhH9ak4'

This will upload all files in the tests directory recursively that regex match
`test_file.txt` to the TEST_FOLDER.
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python cloud_storage/dropbox/upload_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --destination-folder-name TEST_FOLDER --access-key 'fT87blahTblahAAAAAAAblahO54nviTug-n7CblblahpMB6kblahvIqWfhH9ak4'

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python cloud_storage/dropbox/download_file.py --source-file-name-match-type (exact_match/regex_match) --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --connection-string 'SOME-CONNECTION-STRING'

This will download the `test_file.txt` file in the tests/ folder to
the local CWD

venv/bin/python cloud_storage/dropbox/download_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --access-key 'fT87blahTblahAAAAAAAblahO54nviTug-n7CblblahpMB6kblahvIqWfhH9ak4'

This will download all files in the tests/ directory in the tests/ folder
that regex match `test_file.txt` to the local CWD
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python cloud_storage/dropbox/download_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --access-key 'fT87blahTblahAAAAAAAblahO54nviTug-n7CblblahpMB6kblahvIqWfhH9ak4'

```

