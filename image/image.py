import boto3
import json
import os

##############################################
# Event JSON Example                         #
##############################################
#{                                           #
#    "SnapshotID": "snap-0f3e60199f11889da", #
#    "State": "START",                       #
#    "Transitions": 0                        #
#}                                           #
##############################################

def handler(event, context):

    ssm_client = boto3.client('ssm')

    response = ssm_client.get_parameter(
        Name = os.environ['IMAGE_FUNCTION']
    )

    step_function = response['Parameter']['Value']

    sfn_client = boto3.client('stepfunctions')

    sfn_client.start_execution(
        stateMachineArn = step_function,
        input = json.dumps(event)
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Snap4n6 Image')
    }