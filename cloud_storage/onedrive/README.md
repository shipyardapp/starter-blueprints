# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

You will also need to create or use an existing Microsoft account App
that will give you access to a Client ID and Client Secret Key.

Ref: https://www.appypie.com/faqs/how-can-i-get-my-microsoft-acount-client-id-and-client-secret-key

You will also need to set the redirect uri in you Azure Portal after you have
created the app. Under the App under the Authentication tab you can set it
under Platform Configurations as a "Web" Redirect and set it to: http://localhost:8080/

Ref: https://docs.microsoft.com/en-us/onedrive/developer/rest-api/getting-started/msa-oauth?view=odsp-graph-online


# Example Commands
## Upload

For this portion you can assume the **tests/** directory contains the files/subdirs
you wish to upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python cloud_storage/onedrive/upload_file.py --source-file-name-match-type (exact_match/regex_match) --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --client-id CLIENT_ID --client-secret CLIENT_SECRET_KEY 

This will upload the single file `test_file.txt` in the `tests` directory to OneDrive

venv/bin/python cloud_storage/onedrive/upload_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --client-id ExampleClientIDXXXXXXXXXXXXXXXXX --client-secret ExampleClientSecretXXXXXXXXXXXXX

This will upload all files in the tests directory recursively that regex match
`test_file.txt` to OneDrive.
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python cloud_storage/onedrive/upload_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --client-id ExampleClientIDXXXXXXXXXXXXXXXXX --client-secret ExampleClientSecretXXXXXXXXXXXXX

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python cloud_storage/onedrive/download_file.py --source-file-name-match-type (exact_match/regex_match) --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --client-id CLIENT_ID --client-secret CLIENT_SECRET_KEY

This will download the `test_file.txt` file to the local CWD

venv/bin/python cloud_storage/onedrive/download_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --client-id ExampleClientIDXXXXXXXXXXXXXXXXX --client-secret ExampleClientSecretXXXXXXXXXXXXX

This will download all files in the tests/ directory that regex match
`test_file.txt` to the local CWD
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python cloud_storage/onedrive/download_file.py --source-file-name-match-type regex_match --source-file-name test_file.txt --source-folder-name tests/ --client-id ExampleClientIDXXXXXXXXXXXXXXXXX --client-secret ExampleClientSecretXXXXXXXXXXXXX

```

