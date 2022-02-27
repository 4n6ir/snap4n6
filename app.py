#!/usr/bin/env python3
import os

import aws_cdk as cdk

from snap4n6.snap4n6_stack import Snap4N6Stack

app = cdk.App()

Snap4N6Stack(
    app, 'Snap4N6Stack',
    env = cdk.Environment(
        account = os.getenv('CDK_DEFAULT_ACCOUNT'),
        region = os.getenv('CDK_DEFAULT_REGION')
    ),
    synthesizer = cdk.DefaultStackSynthesizer(
        qualifier = '4n6ir'
    )
)

cdk.Tags.of(app).add('snap4n6','snap4n6')

app.synth()
