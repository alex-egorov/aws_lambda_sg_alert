import os
import json
import boto3
import botocore
from datetime import datetime
from pprint import pprint
from deepdiff import DeepDiff

bucket_name  = os.environ.get('BUCKET_NAME', "SecurityGroupsAlertBucket").strip()
mail_from    = os.environ.get('MAIL_FROM', 'from@example.com').strip()
mail_to      = os.environ.get('MAIL_TO', '').strip()

all_regions = "us-east-1, us-east-2, us-west-1, us-west-2, ca-central-1, \
                eu-west-1, eu-central-1, eu-west-2, ap-northeast-1, \
                ap-northeast-2, ap-southeast-1, ap-southeast-2, ap-south-1, \
                sa-east-1"

regions = map(str.strip, os.environ.get('REGIONS' , all_regions).split(','))


#boto3.setup_default_session(profile_name='default')

s3 = boto3.resource('s3')


def lambda_handler(event, context):
    check_all_regions()

def check_all_regions():

    # try to open bucket
    bucket = s3.Bucket(bucket_name)

    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False
            # create bucket
            print "No bucket {}. Trying to create ...".format(bucket_name)
            try:
                response = s3.Bucket(bucket_name).create(
                    ACL='private'
                )
                print "Bucket {} created".format(bucket_name)

            except Exception as e :
                print "Failed to create bucket {}. {}".format(bucket_name, e.args)
                print exit
    except Exception as e:
        print "Unknown error"
        print e.args
        print exit

    changes = False
    report = ''

    for region in regions:
        # Get old data from bucket
        try:
            response = s3.Object(bucket_name, 'security_groups_alert/' + region + '.json').get()
            security_groups_old = json.loads(response['Body'].read())
        except Exception as e:
            print type(e)
            save_data(region, check_region(region))
            continue

        # get security_groups from aws
        security_groups = check_region(region)

        if security_groups_old != security_groups:
            delta = DeepDiff(security_groups_old, security_groups, ignore_order=True)

            report += "\nSECURITY ALERT IN {} ({})\n".format(region, datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"))
            report += "================================================\n\n"

            if delta.get('iterable_item_added'):
                report += parse_data(delta['iterable_item_added'], "Security groups added:")
                changes = True

            if delta.get('iterable_item_removed'):
                report += parse_data(delta['iterable_item_removed'], "Security groups removed:")
                changes = True

            # Save data
            save_data(region, security_groups)
            print "Found changes in {}".format(region)

        else:
            print "No Changes in {}".format(region)

    if changes == True:
        print report
        # Send email
        send_email(report)



def check_region(region):
    # connect to specified region
    ec2 = boto3.resource('ec2', region_name=region)
    ec2client = boto3.client('ec2', region_name=region)

    # get security groups json from aws
    metadata = ec2client.describe_security_groups(
       GroupIds=[],
    )

    # get SecurityGroups
    return metadata['SecurityGroups']


def parse_data (data, header = ''):

    report = "{}\n\n".format(header)

    for key in data:
        ingress = ''
        egress = ''

        sg = data[key]

        for rule in sg['IpPermissions']:
            rule['FromPort']  = rule.get('FromPort', '-')
            rule['ToPort']  = rule.get('ToPort', '-')

            ingress = "%s:%s->%s %s" % (rule['IpProtocol'], \
                                        rule['FromPort'], \
                                        rule['ToPort'], \
                            " ".join(str(item['CidrIp']) for item in rule['IpRanges']) + " " + " ".join(str(item['GroupId']) for item in rule['UserIdGroupPairs']))

        for rule in sg['IpPermissionsEgress']:
            egress = "%s %s" % (rule['IpProtocol'], \
                            " ".join(str(item['CidrIp']) for item in rule['IpRanges']))


        report += "{:>12} {:>12} {:>12} {:<60} {:<20} {:<20}\n".format(sg['VpcId'], sg['OwnerId'], sg['GroupId'], ingress, egress, sg['GroupName'])
        # , sg['Description']

    report += "\n\n"
    return report

def save_data(region, data):
    s3.Object(bucket_name, 'security_groups_alert/' + region + '.json').put(Body=json.dumps(data))
    return


def send_email(message):
    # Send notification email
    if mail_to != '':
        try:
            client = boto3.client('ses', region_name='us-east-1')
            response = client.send_email(
            Source=mail_from,
            Destination={
                'ToAddresses':  [mail_to]
                },
            Message={
                'Subject': {
                    'Data': 'Security Groups Alert'
                },
                'Body': {
                    'Text': {
                        'Data': message
                    }
                }
            })
        except:
            print "Cannot send email"


if __name__ == "__main__":
    check_all_regions()
