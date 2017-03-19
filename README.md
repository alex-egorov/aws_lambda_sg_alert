# Security Groups Alert for AWS

lambda function for aws that checks securyt groups from time to time and
notifies if any changes are found. It uses S3 Bucket to keep previous state
information

## Install

1. Install package DeepDiff into ./lambda folder

    pip install deepdiff -t ./lambda

2. Install [terraform](https://www.terraform.io/downloads.html)

3. Provide AWS credentials for terraform (see details [here](https://www.terraform.io/docs/providers/aws/index.html) )
4. Run

    terraform apply
