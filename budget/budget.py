import boto3
import json

#############################################
# Event JSON Example                        #
#############################################
#{                                          #
#    "SnapshotID": "snap-0f3e60199f11889da" #
#}                                          #
#############################################

def handler(event, context):

    count = 0
    status = 'START'

    ebs_client = boto3.client('ebs')
    
    while(status):
        if status == 'START':
            response = ebs_client.list_snapshot_blocks(
                SnapshotId = event['SnapshotID']
            )
            for block in response['Blocks']:
                count = count + 1
            try:
                status = response['NextToken']
            except:
                status = ''
                continue
        else:
            response = ebs_client.list_snapshot_blocks(
                SnapshotId = event['SnapshotID'],
                NextToken = status
            )
            for block in response['Blocks']:
                count = count + 1
            try:
                status = response['NextToken']
            except:
                status = ''
                continue

    dlsize = (count * response['BlockSize']) / (1024 * 1024 * 1024)
    
    print(' ')
    print('API Quantity: \t'+str(count))
    print('Download Size: \t'+str(round(dlsize,2))+' GB')
    print('Volume Size: \t'+str(response['VolumeSize'])+' GB')
    print(' ')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Snap4n6 Budget')
    }