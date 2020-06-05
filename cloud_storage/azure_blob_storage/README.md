# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

# Example Commands
## Upload

For this portion you can assume the **tests/** directory contains the files/subdirs
you wish to upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python cloud_storage/azure_blob_storage/upload_file.py --container-name CONTAINER_NAME --source-file-name-match-type (exact_match/regex_match) --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --connection-string 'SOME-CONNECTION-STRING'

This will upload the single file `test_file.txt` in the `tests` directory to the 
`shipyard-test` container

venv/bin/python cloud_storage/azure_blob_storage/upload_file.py --container-name shipyard-test --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --connection-string 'DefaultEndpointsProtocol=https;AccountName=testaccountname;AccountKey=some-long-key;EndpointSuffix=core.windows.net'

This will upload all files in the tests directory recursively that regex match
`test_file.txt` to the `shipyard-test` container.
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python cloud_storage/azure_blob_storage/upload_file.py --container-name shipyard-test --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --connection-string 'DefaultEndpointsProtocol=https;AccountName=testaccountname;AccountKey=some-long-key;EndpointSuffix=core.windows.net'

```

