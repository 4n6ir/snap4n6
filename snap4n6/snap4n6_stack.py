import boto3
import sys

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_logs as _logs,
    aws_logs_destinations as _destinations,
    aws_s3 as _s3,
    aws_sns as _sns,
    aws_sns_subscriptions as _subs,
    aws_ssm as _ssm,
    aws_stepfunctions as _sfn,
    aws_stepfunctions_tasks as _tasks
)

from constructs import Construct

class Snap4N6Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        try:
            client = boto3.client('account')
            operations = client.get_alternate_contact(
                AlternateContactType='OPERATIONS'
            )
        except:
            print('Missing IAM Permission --> account:GetAlternateContact')
            sys.exit(1)
            pass

        operationstopic = _sns.Topic(
            self, 'operationstopic'
        )

        operationstopic.add_subscription(
            _subs.EmailSubscription(operations['AlternateContact']['EmailAddress'])
        )

### BUCKET ###

        bucket = _s3.Bucket(
            self, 'bucket',
            encryption = _s3.BucketEncryption.KMS_MANAGED,
            block_public_access = _s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy = RemovalPolicy.DESTROY,
            auto_delete_objects = True,
            versioned = True
        )

        bucketssm = _ssm.StringParameter(
            self, 'bucketssm',
            description = 'Snap4n6 S3 Bucket',
            parameter_name = '/snap4n6/s3/bucket',
            string_value = bucket.bucket_name,
            tier = _ssm.ParameterTier.STANDARD
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
                    'ebs:ListSnapshotBlocks',
                    'ebs:GetSnapshotBlock',
                    's3:PutObject',
                    'ssm:GetParameter',
                    'states:StartExecution'
                ],
                resources = ['*']
            )
        )

        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    'sns:Publish'
                ],
                resources = [
                    operationstopic.topic_arn
                ]
            )
        )

### ERROR ###

        error = _lambda.Function(
            self, 'error',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('error'),
            handler = 'error.handler',
            role = role,
            environment = dict(
                SNS_TOPIC = operationstopic.topic_arn
            ),
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(3),
            memory_size = 128
        )

        errormonitor = _logs.LogGroup(
            self, 'errormonitor',
            log_group_name = '/aws/lambda/'+error.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

### BUDGET ###

        budget = _lambda.Function(
            self, 'budget',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('budget'),
            handler = 'budget.handler',
            timeout = Duration.seconds(900),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 128,
            role = role
        )

        budgetlogs = _logs.LogGroup(
            self, 'budgetlogs',
            log_group_name = '/aws/lambda/'+budget.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        budgetsub = _logs.SubscriptionFilter(
            self, 'budgetsub',
            log_group = budgetlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        budgettime= _logs.SubscriptionFilter(
            self, 'budgettime',
            log_group = budgetlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )

### PASSTHRU ###

        passthru = _lambda.Function(
            self, 'passthru',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('passthru'),
            handler = 'passthru.handler',
            timeout = Duration.seconds(30),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 128,
            role = role
        )

        passthrulogs = _logs.LogGroup(
            self, 'passthrulogs',
            log_group_name = '/aws/lambda/'+passthru.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        passthrusub = _logs.SubscriptionFilter(
            self, 'passthrusub',
            log_group = passthrulogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        passthrutime= _logs.SubscriptionFilter(
            self, 'passthrutime',
            log_group = passthrulogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )

### IMAGE ###

        image = _lambda.Function(
            self, 'image',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('image'),
            handler = 'image.handler',
            timeout = Duration.seconds(30),
            architecture = _lambda.Architecture.ARM_64,
            environment = dict(
                IMAGE_FUNCTION = '/snap4n6/task/image'
            ),
            memory_size = 128,
            role = role
        )

        imagelogs = _logs.LogGroup(
            self, 'imagelogs',
            log_group_name = '/aws/lambda/'+image.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        imagesub = _logs.SubscriptionFilter(
            self, 'imagesub',
            log_group = imagelogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        imagetime= _logs.SubscriptionFilter(
            self, 'imagetime',
            log_group = imagelogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
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
            memory_size = 128,
            role = role
        )

        imagerlogs = _logs.LogGroup(
            self, 'imagerlogs',
            log_group_name = '/aws/lambda/'+imager.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        imagersub = _logs.SubscriptionFilter(
            self, 'imagersub',
            log_group = imagerlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        imagertime= _logs.SubscriptionFilter(
            self, 'imagertime',
            log_group = imagerlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
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
