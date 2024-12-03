import os

import botocore
import aws_cdk as cdk

from askjerm_cdk.askjerm_cdk_stack import AskJermCdkStack, StaticWebsiteStack

app = cdk.App()
ask_jerm_stack = AskJermCdkStack(
    app,
    "AskJermCdkStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

try:
    StaticWebsiteStack(app, "StaticWebsiteStack")
except botocore.exceptions.ClientError:
    print("Deploy AskJermCdkStack using `cdk deploy AskJermCdkStack` then run again`")

app.synth()
