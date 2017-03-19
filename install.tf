provider aws            { }

variable "regions"      { }
variable "bucket_name"  { }
variable "mail_from"    { }
variable "mail_to"      { }

data "archive_file" "lambda_security_groups_alert" {
  type        = "zip"
  source_dir  = "./lambda"
  output_path = "tmp/security_groups_alert.zip"
}

resource "aws_lambda_function" "lambda_security_groups_alert" {
  runtime       = "python2.7"
  timeout       = 10
  memory_size   = 128

  role          = "${aws_iam_role.lambda_security_groups_alert_role.arn}"
  filename      = "${data.archive_file.lambda_security_groups_alert.output_path}"
  function_name = "security_groups_alert_function"
  handler       = "security_groups_alert.lambda_handler"

  source_code_hash = "${data.archive_file.lambda_security_groups_alert.output_base64sha256}"

  environment {
    variables = {
      REGIONS      = "${var.regions}"
      BUCKET_NAME  = "${var.bucket_name}"
      MAIL_FROM    = "${var.mail_from}"
      MAIL_TO      = "${var.mail_to}"
    }
  }
}

###################################### IAM #####################################
resource "aws_iam_role_policy" "lambda_security_groups_alert_policy" {
  name = "lambda_security_groups_alert"
  role = "${aws_iam_role.lambda_security_groups_alert_role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSecurityGroups",
        "s3:CreateBucket",
        "s3:GetObject",
        "s3:PutObject",
        "ses:SendEmail"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role" "lambda_security_groups_alert_role" {
  name = "iam_lambda_security_groups_alert_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

################################# CLOUD WATCH ##################################

resource "aws_cloudwatch_event_rule" "lambda_security_groups_alert_rule" {
  name                = "lambda_security_groups_alert"
  description         = "Event rule for Lambda Security Groups Alert"
  schedule_expression = "cron(10 1 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_security_groups_alert_target" {
  rule      = "${aws_cloudwatch_event_rule.lambda_security_groups_alert_rule.name}"
  target_id = "lambda_security_groups_alert_target"
  arn       = "${aws_lambda_function.lambda_security_groups_alert.arn}"
}

resource "aws_lambda_permission" "lambda_security_groups_alert_permission" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.lambda_security_groups_alert.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.lambda_security_groups_alert_rule.arn}"
}
