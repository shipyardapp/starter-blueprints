# Setup

```
git clone https://github.com/shipyardapp/starter-blueprints.git
cd starter-blueprints/
python3.7 -m venv venv
venv/bin/python setup.py install
```

You will need the ftp server hostname/address as well as port if it's not the
default ftp port(21) as well as the user credentials

# Example Commands
## Upload

For this portion you can assume the **tests/** directory contains the files/subdirs
you wish to upload

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python ftp/ftp/upload_file.py --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --source-file-name-match-type (exact_match/regex_match) --destination-folder-name DESTINATION_FOLDER --host 'SERVER_HOSTNAME' --port FTP_PORT --username 'USERNAME' --password 'FTP_PASSWORD' 

This will upload the single file `test_file.txt` in the `tests` directory to the 
`ftp_folder` on the FTP server

venv/bin/python ftp/ftp/upload_file.py --source-file-name 'test_file.txt' --source-folder-name tests/ --source-file-name-match-type 'exact_match' --destination-folder-name 'ftp_folder' --host 'ftp.hostname.address' --port 1234 --username 'USERNAME' --password 'PASSWORD1234' 

This will upload all files in the tests directory recursively that regex match
`test_file.txt` to the `ftp_folder` on the FTP server.
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python ftp/ftp/upload_file.py --source-file-name 'test_file.txt*' --source-folder-name tests/ --source-file-name-match-type 'regex_match' --destination-folder-name 'ftp_folder' --host 'ftp.hostname.address' --port 1234 --username 'USERNAME' --password 'PASSWORD1234' 

```

## Download

From the `starter-blueprints/` directory
```
Demo command

venv/bin/python ftp/ftp/download_file.py --source-file-name-match-type (exact_match/regex_match) --source-file-name SOURCE_NAME --source-folder-name SOURCE_FOLDER --host 'SERVER_HOSTNAME' --port FTP_PORT --username 'USERNAME' --password 'FTP_PASSWORD' 

This will download the `test_file.txt` file in the `ftp_folder` on the FTP
server to the local CWD

venv/bin/python ftp/ftp/download_file.py --source-file-name 'test_file.txt' --source-folder-name ftp_folder --source-file-name-match-type 'exact_match' --host 'ftp.hostname.address' --port 1234 --username 'USERNAME' --password 'PASSWORD1234' 

This will download all files in the `ftp_folder` directory that regex match
`test_file.txt` to the local CWD
i.e. `test_file.txt-bu`, `test_file.txt123`, etc

venv/bin/python ftp/ftp/download_file.py --source-file-name 'test_file.txt' --source-folder-name ftp_folder --source-file-name-match-type 'regex_match' --host 'ftp.hostname.address' --port 1234 --username 'USERNAME' --password 'PASSWORD1234' 

```

