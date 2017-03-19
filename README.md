# Security Groups Alert for AWS

lambda function for aws that checks securyt groups from time to time and
notifies if any changes are found. It uses S3 Bucket to keep previous state
information

## Install

1. Install package DeepDiff into ./lambda folder

    pip install deepdiff -t ./lambda

2. Install [terraform](https://www.terraform.io/downloads.html)

3. Create terraform.tfvars file with following variables:

```
regions      = "us-west-2, us-east-1"
bucket_name  = "yourbuckername"
mail_to      = "you@yourmail.com"
mail_from    = "from@mail.com"
```

Script uses SES service to send emails, so mail address should be validated.

or define them in terraform in any other way

4. Provide AWS credentials for terraform (see details [here](https://www.terraform.io/docs/providers/aws/index.html) )

5. Run

    terraform apply
