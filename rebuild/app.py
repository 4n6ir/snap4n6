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
    filevalue = output[2].split('_')

    os.system('dd if=/dev/zero of=/tmp/'+event['SnapshotID']+'.dd bs=1 count=0 seek='+filevalue[3]+'G')

    if event['FileSystemExt4'] == 'Yes':
        os.system('echo y | /usr/sbin/mkfs.ext4 /tmp/'+event['SnapshotID']+'.dd')

    s3_client.upload_file(
        '/tmp/'+event['SnapshotID']+'.dd',
        os.environ['BUCKET_NAME'],
        'image/'+event['SnapshotID']+'/'+event['SnapshotID']+'.dd'
    )





    return {
        'statusCode': 200,
        'body': json.dumps('Snap4n6 Rebuild')
    }