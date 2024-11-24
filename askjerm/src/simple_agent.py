"""
Simple invocation of agent
"""
import boto3


def load_config(file_path):
    # load environmental variables from config file
    config = {}
    with open(file_path) as fid:
        for line in fid:
            # Ignore empty lines and comments
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip().strip('"')
    return config


config = load_config(".config")

# MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"
AWS_REGION = config.get("AWS_REGION")
AGENT_ID = config.get("AGENT_ID")
ALIAS_ID = config.get("ALIAS_ID")

# client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
client = boto3.client("bedrock-agent-runtime")

user_query = "Who is Jeremy?"
# user_query = "Who are you?"

response = client.invoke_agent(
    agentAliasId=ALIAS_ID,
    agentId=AGENT_ID,
    inputText=user_query,
    sessionId="abc123",
)
for event in response["completion"]:
    print(event["chunk"]["bytes"].decode("utf-8"))
