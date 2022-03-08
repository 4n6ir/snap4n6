import boto3
import json
import os

def handler(event, context):

    s3_client = boto3.client('s3')
    
    s3_client.download_file(
        os.environ['BUCKET_NAME'],
        'image/'+event['SnapshotID']+'/'+event['SnapshotID']+'.dd',
        '/mnt/snapshot/'+event['SnapshotID']+'.dd'
    )
    
    os.system('cd /mnt/snapshot && ls -lh')
    
    ssm_client = boto3.client('ssm')

    response = ssm_client.get_parameter(
        Name = os.environ['REBUILD_FUNCTION']
    )

    step_function = response['Parameter']['Value']
    
    sfn_client = boto3.client('stepfunctions')

    sfn_client.start_execution(
        stateMachineArn = step_function,
        input = json.dumps(event)
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Snap4n6 Transfer')
    }