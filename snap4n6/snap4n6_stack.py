from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2 as _ec2,
    aws_efs as _efs,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_logs as _logs,
    aws_s3 as _s3,
    aws_ssm as _ssm,
    aws_stepfunctions as _sfn,
    aws_stepfunctions_tasks as _tasks
)

from constructs import Construct

class Snap4N6Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

### BUCKET ###

        bucket = _s3.Bucket(
            self, 'bucket',
            encryption = _s3.BucketEncryption.KMS_MANAGED,
            block_public_access = _s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy = RemovalPolicy.DESTROY,
            auto_delete_objects = True,
            versioned = True
        )

### ROLE ###

        role = _iam.Role(
            self, 'role', 
            assumed_by = _iam.ServicePrincipal(
                'lambda.amazonaws.com'
            )
        )
        
        role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSLambdaBasicExecutionRole'
            )
        )

        role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSLambdaVPCAccessExecutionRole'
            )
        )

        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    'ebs:ListSnapshotBlocks',
                    'ebs:GetSnapshotBlock',
                    's3:PutObject',
                    'ssm:GetParameter',
                    'states:StartExecution'
                ],
                resources = ['*']
            )
        )

### ISOLATED VPC ###

        vpc = _ec2.Vpc(
            self, 'vpc',
            cidr = '192.168.242.0/24',
            max_azs = 1,
            nat_gateways = 0,
            enable_dns_hostnames = True,
            enable_dns_support = True,
            subnet_configuration = [
                _ec2.SubnetConfiguration(
                    subnet_type = _ec2.SubnetType.PRIVATE_ISOLATED,
                    name = 'isolated',
                    cidr_mask = 24
                )
            ],
            gateway_endpoints = {
                'S3': _ec2.GatewayVpcEndpointOptions(
                    service = _ec2.GatewayVpcEndpointAwsService.S3
                )
            }
        )
        
        ### NOT SUPPORTED ###
        #vpc.add_interface_endpoint(
        #    'ElasticBlockStorageEndpoint',
        #    service = _ec2.InterfaceVpcEndpointAwsService.EBS
        #)

### BUDGET ###

        budget = _lambda.Function(
            self, 'budget',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('budget'),
            handler = 'budget.handler',
            timeout = Duration.seconds(900),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 512,
            role = role,
            #vpc = vpc
        )
        
        budgetlogs = _logs.LogGroup(
            self, 'budgetlogs',
            log_group_name = '/aws/lambda/'+budget.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )
        
        budgetmonitor = _ssm.StringParameter(
            self, 'budgetmonitor',
            description = 'Snap4n6 Budget Monitor',
            parameter_name = '/snap4n6/monitor/budget',
            string_value = '/aws/lambda/'+budget.function_name,
            tier = _ssm.ParameterTier.STANDARD
        )

### PASSTHRU ###

        passthru = _lambda.Function(
            self, 'passthru',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('passthru'),
            handler = 'passthru.handler',
            timeout = Duration.seconds(900),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 512,
            role = role
        )
        
        passthrulogs = _logs.LogGroup(
            self, 'passthrulogs',
            log_group_name = '/aws/lambda/'+passthru.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )
        
        passthrumonitor = _ssm.StringParameter(
            self, 'passthrumonitor',
            description = 'Snap4n6 PassThru Monitor',
            parameter_name = '/snap4n6/monitor/passthru',
            string_value = '/aws/lambda/'+passthru.function_name,
            tier = _ssm.ParameterTier.STANDARD
        )

### IMAGE ###

        image = _lambda.Function(
            self, 'image',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('image'),
            handler = 'image.handler',
            timeout = Duration.seconds(900),
            architecture = _lambda.Architecture.ARM_64,
            environment = dict(
                IMAGE_FUNCTION = '/snap4n6/task/image'
            ),
            memory_size = 512,
            role = role
        )
        
        imagelogs = _logs.LogGroup(
            self, 'imagelogs',
            log_group_name = '/aws/lambda/'+image.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )
        
        imagemonitor = _ssm.StringParameter(
            self, 'imagemonitor',
            description = 'Snap4n6 Image Monitor',
            parameter_name = '/snap4n6/monitor/image',
            string_value = '/aws/lambda/'+image.function_name,
            tier = _ssm.ParameterTier.STANDARD
        )

### IMAGER ###

        imager = _lambda.Function(
            self, 'imager',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('imager'),
            handler = 'imager.handler',
            timeout = Duration.seconds(900),
            architecture = _lambda.Architecture.ARM_64,
            environment = dict(
                BUCKET_NAME = bucket.bucket_name,
                IMAGE_FUNCTION = '/snap4n6/task/image'
            ),
            memory_size = 512,
            role = role,
            #vpc = vpc
        )
        
        imagerlogs = _logs.LogGroup(
            self, 'imagerlogs',
            log_group_name = '/aws/lambda/'+imager.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )
        
        imagermonitor = _ssm.StringParameter(
            self, 'imagermonitor',
            description = 'Snap4n6 Imager Monitor',
            parameter_name = '/snap4n6/monitor/imager',
            string_value = '/aws/lambda/'+imager.function_name,
            tier = _ssm.ParameterTier.STANDARD
        )

### IMAGE FUNCTION ###

        initial = _tasks.LambdaInvoke(
            self, 'initial',
            lambda_function = passthru,
            output_path = '$.Payload',
        )

        imaging = _tasks.LambdaInvoke(
            self, 'imaging',
            lambda_function = imager,
            output_path = '$.Payload',
        )

        failed = _sfn.Fail(
            self, 'failed',
            cause = 'Failed',
            error = 'FAILED'
        )

        succeed = _sfn.Succeed(
            self, 'succeeded',
            comment = 'SUCCEEDED'
        )

        definition = initial.next(imaging) \
            .next(_sfn.Choice(self, 'Completed?')
                .when(_sfn.Condition.string_equals('$.status', 'FAILED'), failed)
                .when(_sfn.Condition.string_equals('$.status', 'SUCCEEDED'), succeed)
                .otherwise(imaging)
            )
            
        statelogs = _logs.LogGroup(
            self, 'statelogs',
            log_group_name = '/aws/state/snap4n6image',
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )
            
        state = _sfn.StateMachine(
            self, 'snap4n6image',
            definition = definition,
            logs = _sfn.LogOptions(
                destination = statelogs,
                level = _sfn.LogLevel.ALL
            )
        )

        statessm = _ssm.StringParameter(
            self, 'statessm',
            description = 'Snap4n6 Image State',
            parameter_name = '/snap4n6/task/image',
            string_value = state.state_machine_arn,
            tier = _ssm.ParameterTier.STANDARD
        )

### SNAPSHOT IMAGE ###

        efs = _efs.FileSystem(
            self, 'efs', 
            vpc = vpc,
            removal_policy = RemovalPolicy.DESTROY
        )

        access = efs.add_access_point(
            'AccessPoint',
            path = '/export/snapshot',
            create_acl = _efs.Acl(
                owner_uid = '1001',
                owner_gid = '1001',
                permissions = '750'
            ),
            posix_user = _efs.PosixUser(
                uid = '1001',
                gid = '1001'
            )
        )

