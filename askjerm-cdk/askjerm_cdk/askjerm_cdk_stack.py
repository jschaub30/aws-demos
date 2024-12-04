import boto3
from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from cdklabs.generative_ai_cdk_constructs import bedrock
from constructs import Construct


def read_stack_output(stack_name, key):
    """read output value from a deployed stack"""
    client = boto3.client("cloudformation")

    # Get the stack details
    response = client.describe_stacks(StackName=stack_name)
    stacks = response.get("Stacks", [])
    if not stacks:
        print(f"No stack found with name: {stack_name}")
        return None

    # Fetch outputs
    stack = stacks[0]
    outputs = stack.get("Outputs", [])
    for output in outputs:
        output_key = output.get("OutputKey")
        if output_key == key:
            return output.get("OutputValue")
    print(f"No key found named {key!r}")
    return None


class AskJermCdkStack(Stack):
    """
    Deploy AI Agent (knowledge base, data source, agent) and lambda function
    to invoke the agent
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        kb_prompt = (
            "Use this knowledge base to answer questions about Jeremy "
            + "Schaub's professional career"
        )

        kb = bedrock.KnowledgeBase(
            self,
            "KnowledgeBase",
            embeddings_model=bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V2_1024,
            instruction=kb_prompt,
        )

        bucket = s3.Bucket(
            self,
            "ask-jerm",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        BucketDeployment(
            self,
            "DeployDocuments",
            sources=[Source.asset("./documents")],
            destination_bucket=bucket,
        )

        kb.add_s3_data_source(
            bucket=bucket,
            chunking_strategy=bedrock.ChunkingStrategy.SEMANTIC,
            data_source_name="Jerm_documents",
        )
        kb.add_web_crawler_data_source(
            source_urls=["https://jeremyschaub.us"],
            chunking_strategy=bedrock.ChunkingStrategy.HIERARCHICAL_TITAN,
        )

        agent_prompt = (
            "You are a helpful and friendly agent named Jerm."
            "You represent Jeremy Schaub, who is applying for jobs. "
        )
        agent = bedrock.Agent(
            self,
            "Agent",
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=agent_prompt,
            alias_name="latest",
            should_prepare_agent=True,
        )
        agent.add_knowledge_base(kb)

        function = _lambda.Function(
            self,
            "AskJerm",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda.lambda_handler",
            code=_lambda.Code.from_asset("src"),
            timeout=Duration.seconds(30),
        )

        bedrock_policy = PolicyStatement(
            actions=["bedrock:InvokeAgent"],
            resources=[agent.agent_arn, agent.alias_arn],
        )
        function.add_to_role_policy(bedrock_policy)

        function.add_environment("AGENT_ID", agent.agent_id)
        function.add_environment("ALIAS_ID", agent.alias_id)

        function_url = function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
        )

        CfnOutput(
            self,
            "LambdaFunctionUrl",
            value=function_url.url,
            description="The URL of the Lambda function to invoke the Agent",
        )


class StaticWebsiteStack(Stack):
    # S3 bucket to host AskJerm web client
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(
            self,
            "StaticWebsiteBucket",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # inject the Lambda function URL into index.html
        with open("src/webapp/index_template.html") as file:
            index_content = file.read()

            # Replace the placeholder with the actual Lambda URL
            lambda_function_url = read_stack_output(
                "AskJermCdkStack", "LambdaFunctionUrl"
            )
            if not lambda_function_url:
                raise Exception(
                    "Problem reading lambda function URL from AskJerm stack"
                )
            index_content = index_content.replace(
                "LAMBDA_URL_PLACEHOLDER", lambda_function_url
            )

            # Save the transformed file
            transformed_path = "src/webapp/index.html"
            with open(transformed_path, "w") as file:
                file.write(index_content)

        # Deploy local files
        BucketDeployment(
            self,
            "DeployWebsite",
            sources=[Source.asset("src/webapp/")],
            destination_bucket=bucket,
        )

        CfnOutput(
            self,
            "WebsiteURL",
            value=bucket.bucket_website_url,
            description="URL for the static website",
        )
