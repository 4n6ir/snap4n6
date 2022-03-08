#import boto3
#import hashlib
#import io
import json
#import os

def handler(event, context):

    snapid = event['event']['SnapshotID']
    filesystem = event['event']['FileSystemExt4']
    state = event['event']['State']
    transitions = event['event']['Transitions']
    
    #limit = 'NO'
    
    #ebs_client = boto3.client('ebs')
    #s3_client = boto3.client('s3')
    
    if state == 'START':



    else:



    #status = 'CONTINUE'
    #status = 'SUCCEEDED'

    
    #transitions += 1
    
    #if transitions == 2500:
        
    #    limit = 'YES'
    #    transitions = 0
    
    event = {}
    event['SnapshotID'] = snapid
    event['FileSystemExt4'] = filesystem
    event['State'] = state
    event['Transitions'] = transitions

    
    #if limit == 'YES':
        
    #    ssm_client = boto3.client('ssm')

    #    response = ssm_client.get_parameter(
    #        Name = os.environ['IMAGE_FUNCTION']
    #    )

    #    step_function = response['Parameter']['Value']

    #    sfn_client = boto3.client('stepfunctions')

    #    sfn_client.start_execution(
    #        stateMachineArn = step_function,
    #        input = json.dumps(event)
    #    )
   
    #    status = 'SUCCEEDED'
    
    return {
        'event': event,
        'status': status,
    }