import os
import json
import logging
from base64 import b64decode
from urllib.parse import parse_qs, unquote_plus
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DELIVER_TO = os.environ.get("DELIVER_TO")
client = boto3.client('ses', region_name='us-east-1')

def lambda_handler(event, context):
    logger.debug(json.dumps(event))
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        'Content-Type': 'text/html'
    }

    # Parse the incoming payload
    if event.get("isBase64Encoded"):
        body = b64decode(event['body']).decode('utf-8')  # decode base64 string
        body = unquote_plus(body)  # decode the percent-encoded characters and + signs
        body = parse_qs(body)      # to dict
    elif isinstance(event["body"], dict):
        body = event["body"]
    elif event['body']:
        body = json.loads(event['body'])
    else:
        body = None

    if not body or 'name' not in body or 'email' not in body or 'message' not in body:
        msg = "Must provide 'name', 'email' and 'message' in body"
        return {
            'statusCode': 500,
            'headers': headers,
            'body': msg,
        }
    name = body['name']
    email = body['email']
    message = body['message']

    print(f"Name: {name}, Email: {email}, Message: {message}")

    msg = f"name: {name}\n"
    msg += f"email: {email}\n"
    msg += f"message: {message}"

    try:
        client.send_email(
            Destination={
                'ToAddresses': [DELIVER_TO]
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': msg,
                    }
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': 'SES message received: ' + message[:16],
                },
            },
            Source=DELIVER_TO
        )

        html_content = """
        <html>
            <head>
                <title>Confirmation</title>
            </head>
            <body>
                <p>Thank you for reaching out! I'll be in touch within a day or two.</p>
            </body>
        </html>
        """
        logger.info(f"Success sending email with msg: {msg}")

        return {
            'statusCode': 200,
            'headers': headers,
            'body': html_content
        }
    except Exception as e:
        msg = f"Problem sending email: {str(e)}"
        logger.error(msg)
        return {
            'statusCode': 500,
            'headers': headers,
            'body': msg,
        }
