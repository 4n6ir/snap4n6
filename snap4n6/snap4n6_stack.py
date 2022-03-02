from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_logs as _logs,
    aws_s3 as _s3,
    aws_ssm as _ssm
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

        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    'ebs:ListSnapshotBlocks'
                ],
                resources = ['*']
            )
        )

### BUDGET ###

        budget = _lambda.Function(
            self, 'budget',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('budget'),
            handler = 'budget.handler',
            timeout = Duration.seconds(900),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 512,
            role = role
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
