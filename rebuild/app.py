import boto3
import json
import os

##############################################
# Event JSON Example                         #
##############################################
#{                                           #
#    "SnapshotID": "snap-0f3e60199f11889da", #
#    "FileSystemExt4": "Yes",                #
#    "Transitions": 0                        #
#}                                           #
##############################################

def lambdaHandler(event, context):

    s3_client = boto3.client('s3')

    response = s3_client.list_objects_v2(
        Bucket = os.environ['BUCKET_NAME'],
        MaxKeys = 1,
        Prefix = 'raw/'+event['SnapshotID']+'/',
    )

    output = response['Contents'][0]['Key'].split('/')
    print(output[2])




    return {
        'statusCode': 200,
        'body': json.dumps('Snap4n6 Rebuild')
    }