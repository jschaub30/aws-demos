#!/usr/bin/env python3
import os

import aws_cdk as cdk

from askjerm_cdk.askjerm_cdk_stack import AskJermCdkStack

app = cdk.App()
AskJermCdkStack(
    app,
    "AskJermCdkStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
