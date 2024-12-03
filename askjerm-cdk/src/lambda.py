import json
import logging
import os
from base64 import b64decode
from urllib.parse import parse_qs, unquote_plus

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AGENT_ID = os.environ.get("AGENT_ID")
ALIAS_ID = os.environ.get("ALIAS_ID")


def invoke_agent(user_query):
    client = boto3.client("bedrock-agent-runtime")
    try:
        # Invoke the bedrock agent
        response = client.invoke_agent(
            agentAliasId=ALIAS_ID,
            agentId=AGENT_ID,
            inputText=user_query,
            sessionId="abc123",
        )
    except Exception as e:
        msg = f"Error invoking agent: {str(e)}"
        logger.error(msg)
        return {"success": False, "message": msg}
    logger.debug("Response of agent request:", response)
    event_stream = response["completion"]
    answer = ""
    

    for event in event_stream:
        if "chunk" in event:
            answer += event["chunk"]["bytes"].decode("utf-8")
        elif "trace" in event:
            logger.info(event["trace"])
            return {"success": False, "message": f"ERROR: {event["trace"].get("failureTrace")}"}
    return {"success": True, "message": answer}


def lambda_handler(event, context):
    logger.debug(json.dumps(event))
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "text/html",
    }

    if event.get("requestContext") and event["requestContext"].get("http"):
        http_method = event["requestContext"]["http"].get("method")

        print(f"HTTP Method: {http_method}")
        if http_method == "OPTIONS":  # need to return 200 OK
            return {
                "statusCode": 200,
                "headers": headers,
                "body": "",
            }

    # Parse the incoming payload
    if event.get("isBase64Encoded"):
        body = b64decode(event["body"]).decode("utf-8")  # decode base64 string
        body = unquote_plus(body)  # decode the percent-encoded characters and + signs
        body = parse_qs(body)  # to dict
    elif "body" not in event:
        body = None
    elif isinstance(event["body"], dict):
        body = event["body"]
    elif event["body"]:
        body = json.loads(event["body"])
        

    if not body or "inputText" not in body:
        msg = "Must provide 'inputText' in body"
        logger.error(msg)
        return {
            "statusCode": 500,
            "headers": headers,
            "body": msg,
        }

    user_query = body.get("inputText", None)
    print(f"Invoking agent with query: {user_query}")
    result = invoke_agent(user_query)
    if result.get("success"):
        return {
            "statusCode": 200,
            "headers": headers,
            "body": result.get("message"),
        }
    return {
        "statusCode": 500,
        "headers": headers,
        "body": result.get("message"),
    }

