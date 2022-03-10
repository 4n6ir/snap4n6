import boto3
import gzip
import hashlib
import io
import json
import os

def handler(event, context):

    snapid = event['event']['SnapshotID']
    state = event['event']['State']
    transitions = event['event']['Transitions']
    
    limit = 'NO'
    
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
    			with io.FileIO('/tmp/'+snapid+'.tmp', 'rb') as r:
    			    with gzip.open('/tmp/'+fname+'.gz','wb') as w:
    			        for b in r:
    			            w.write(b)
    			    w.close()
    			r.close()
    			s3_client.upload_file('/tmp/'+fname+'.gz', os.environ['BUCKET_NAME'], snapid+'/'+fname+'.gz')
    			os.system('rm /tmp/'+fname+'.gz')
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
    			with io.FileIO('/tmp/'+snapid+'.tmp', 'rb') as r:
    			    with gzip.open('/tmp/'+fname+'.gz','wb') as w:
    			        for b in r:
    			            w.write(b)
    			    w.close()
    			r.close()
    			s3_client.upload_file('/tmp/'+fname+'.gz', os.environ['BUCKET_NAME'], snapid+'/'+fname+'.gz')
    			os.system('rm /tmp/'+fname+'.gz')
    		try:
    			state = response['NextToken']
    			status = 'CONTINUE'
    		except:
    			state = ''
    			status = 'SUCCEEDED'
    			continue
    
    transitions += 1
    
    if transitions == 2500:
        
        limit = 'YES'
        transitions = 0
    
    event = {}
    event['SnapshotID'] = snapid
    event['State'] = state
    event['Transitions'] = transitions

    if limit == 'YES':
        
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
        
        status = 'SUCCEEDED'
    
    return {
        'event': event,
        'status': status,
    }