from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from cdklabs.generative_ai_cdk_constructs import bedrock
from constructs import Construct


class AskJermCdkStack(Stack):
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

        bedrock.S3DataSource(
            self,
            "DataSource",
            bucket=bucket,
            knowledge_base=kb,
            data_source_name="askjerm",
            chunking_strategy=bedrock.ChunkingStrategy.FIXED_SIZE,
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
