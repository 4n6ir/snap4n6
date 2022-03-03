import boto3
import hashlib
import io
import json
import os

def handler(event, context):

    snapid = event['event']['SnapshotID']
    state = event['event']['State']
    
    ebs_client = boto3.client('ebs')
    s3_client = boto3.client('s3')
    
    while(state):
    	if state == 'START':
    		response = ebs_client.list_snapshot_blocks(
    			SnapshotId = snapid
    		)
    		for block in response['Blocks']:
    			download = ebs_client.get_snapshot_block(
    				SnapshotId = snapid,
    				BlockIndex = block['BlockIndex'],
    				BlockToken = block['BlockToken']
    			)
    			sha256_hash = hashlib.sha256()
    			with io.FileIO('/tmp/'+snapid+'.tmp', 'wb') as f:
    				for b in download['BlockData']:
    					sha256_hash.update(b)
    					f.write(b)
    			f.close()
    			fname = str(block['BlockIndex']).zfill(10)+'_'+snapid+'_'+sha256_hash.hexdigest()+'_'+str(response['VolumeSize'])+'_'+str(response['BlockSize'])
    			s3_client.upload_file('/tmp/'+snapid+'.tmp', os.environ['BUCKET_NAME'], 'raw/'+snapid+'/'+fname)
    		try:
    			state = response['NextToken']
    			status = 'CONTINUE'
    		except:
    			state = ''
    			status = 'SUCCEEDED'
    			continue
    	else:
    		response = ebs_client.list_snapshot_blocks(
    			SnapshotId = snapid,
    			NextToken = state
    		)
    		for block in response['Blocks']:
    			download = ebs_client.get_snapshot_block(
    				SnapshotId = snapid,
    				BlockIndex = block['BlockIndex'],
    				BlockToken = block['BlockToken']
    			)
    			sha256_hash = hashlib.sha256()
    			with io.FileIO('/tmp/'+snapid+'.tmp', 'wb') as f:
    				for b in download['BlockData']:
    					sha256_hash.update(b)
    					f.write(b)
    			f.close()
    			fname = str(block['BlockIndex']).zfill(10)+'_'+snapid+'_'+sha256_hash.hexdigest()+'_'+str(response['VolumeSize'])+'_'+str(response['BlockSize'])
    			s3_client.upload_file('/tmp/'+snapid+'.tmp', os.environ['BUCKET_NAME'], 'raw/'+snapid+'/'+fname)						
    		try:
    			state = response['NextToken']
    			status = 'CONTINUE'
    		except:
    			state = ''
    			status = 'SUCCEEDED'
    			continue

    event = {}
    event['SnapshotID'] = snapid
    event['State'] = state

    return {
        'event': event,
        'status': status,
    }