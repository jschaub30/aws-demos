from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from cdklabs.generative_ai_cdk_constructs import bedrock
from constructs import Construct


class CdkStack(Stack):
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

        bucket = s3.Bucket(self, "ask-jerm")

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
