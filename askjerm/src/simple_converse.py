"""
Simple conversation using prompts
No knowledge bases
"""

AWS_REGION = "us-west-2"
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

SYSTEM_PROMPT = """
Your name is Jeremy.
You are applying for jobs.
"""

import boto3
from botocore.exceptions import ClientError

def converse(user_message):
    """converse script"""

    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]
    system_prompt = [{"text": SYSTEM_PROMPT}]

    try:
        # Send the message to the model, using a basic inference configuration.
        response = client.converse(
            modelId=MODEL_ID,
            messages=conversation,
            system=system_prompt,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )

        # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        print(response_text)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{MODEL_ID}'. Reason: {e}")
        exit(1)

if __name__ == "__main__":
    converse("What is your name?")
