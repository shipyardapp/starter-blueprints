To get a general feel for what the final product of an expectation suite will look like, we created an example expectation suite that looks at [Amazon's Product Review data](https://s3.amazonaws.com/amazon-reviews-pds/readme.html). This file includes:

- The minimum required directories and scripts needed to run Great Expectations.
- An Expectation Suite called `amazon-product-reviews`
- A script called `run_great_expectations.py` that:
  - Pulls down the external data of Amazon Product Reviews using a public S3 URL.
  - Decompresses the file and converts it to a CSV (a requirement to get this specific data set working)
  - Runs the data through your Expectation Suite.
  - Stores the json output externally in an S3 bucket, with dynamically generated IDs.
  - Conditionally triggers exit codes based on the JSON output.

A few interesting notes about the setup process:

- For your expectation suites to work, they'll have to live in a directory called `great_expectations` and follow other required directory naming conventions.
- We created a datasource called `root` in `great_expectations.yml` that will recognize any files that exist in the root directory. This minimizes the setup of adding more and more datasets and makes it easier to download data externally and run it against your expectations immediately.
- Great expectations only has built-in support for file storage on S3 right now. If you'd like to store files elsewhere (Google Cloud Storage, Azure Blob Storage, Dropbox, Google Drive, Box, etc.), you can replace the `upload_to_s3` function with something else.
- For our example, the input url can be any of the URLs listed [here](https://s3.amazonaws.com/amazon-reviews-pds/tsv/index.txt).

To run your expectation suite locally, you'll need to set up the following things:

1. Unzip the the file and navigate to that directory in your terminal.
2. Create a virtual environment and install the following 4 packages:
   boto3==1.12.16
   great-expectations==0.9.5
   pandas==1.0.1
   wget==3.2

Note: We didn't include a requirements.txt file to specifically maintain the visibility of package requirements within the Shipyard interface.

3. Create a new S3 bucket, or use an existing S3 bucket, to store generated validation files. Using the credentials for the IAM role that accesses this bucket, add environment variables to your computer for `GREAT_EXPECTATIONS_AWS_ACCESS_KEY_ID` and `GREAT_EXPECTATIONS_AWS_SECRET_ACCESS_KEY`.

Note: This step is not necessary if you don't include the `--output_bucket_name` argument. However, your validation results will only be stored locally.

4. Run the following command.

   python run_great_expectations.py \
    --input_url https://s3.amazonaws.com/amazon-reviews-pds/tsv/sample_us.tsv \
    --output_bucket_name <your-bucket-name> \
    --expectation_suite amazon-product-reviews

5. Success! You can now run `great_expectations docs build` to view all of the expectations visually, alongside the most recent validation run.
