import aws_cdk as core
import aws_cdk.assertions as assertions
from askjerm_cdk.askjerm_cdk_stack import AskJermCdkStack


def test_s3_retention():
    app = core.App()
    stack = AskJermCdkStack(app, "cdk")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::S3::Bucket", {"DeletionPolicy": "Delete"})


if __name__ == "__main__":
    test_s3_retention()
