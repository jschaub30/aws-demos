"""
Creates job in DDB table, and either:
- generates a presigned URL for the client to upload, or 
- downloads from an existing URL, and uploads to the input bucket
"""
import json
import logging
import os
import time
import uuid
import mimetypes
from datetime import datetime

import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
table_name = os.environ.get("TABLE_NAME")
TABLE = dynamodb.Table(table_name)
TTL_DAYS = 30  # DynamoDB data time-to-live


def lambda_handler(event, context):
    bucket_name = os.environ.get("BUCKET_NAME")
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if not bucket_name:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps(
                {"message": "Bucket name not set in environment variables"}
            ),
        }

    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)

    if body is None or ("filename" not in body and "source_url" not in body):
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps(
                {
                    "message": "Must provide 'filename' and 'content_type' "
                    + "OR 'source_url' in body"
                }
            ),
        }

    job_id = body["job_id"] if "job_id" in body else str(uuid.uuid4())[:8]

    if "filename" in body:
        return gen_presigned_url(body, job_id, bucket_name, headers)
    elif "source_url" in body:
        return copy_to_bucket(body, job_id, bucket_name, headers)


def gen_presigned_url(body, job_id, bucket_name, headers):
    """Handles the file upload from filename and content_type."""
    object_key = f"input/{job_id}/{body['filename']}"
    content_type = body["content_type"]
    create_job(job_id, bucket_name, object_key)

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,  # URL expiration time in seconds
            HttpMethod="PUT",
        )
    except Exception as e:
        message = f"Error generating presigned URL: {str(e)}"
        update_job(job_id, "error", message=message)
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": message}),
        }

    result = {"presigned_url": presigned_url, "job_id": job_id}
    return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}


def copy_to_bucket(body, job_id, bucket_name, headers):
    """Handles the download from source_url and upload to the bucket."""
    source_url = body["source_url"]
    fname = source_url.split("?")[0].rsplit("/", 1)[1]
    object_key = f"input/{job_id}/{fname}"
    create_job(job_id, bucket_name, object_key)

    try:
        # Download the file from source_url
        result = download_file_from_url(source_url)
        file_content = result["content"]
        if file_content is None:
            message = f"Error downloading file from {source_url}: no content"
            update_job(job_id, "error", message=message)
            return {
                "statusCode": 500,
                "headers": headers,
                "body": json.dumps({"message": message}),
            }

        # Upload the file to S3
        upload_file_to_s3(bucket_name, object_key, file_content, result["content_type"])

    except Exception as e:
        message = f"Error processing source_url: {str(e)}"
        update_job(job_id, "error", message=message)
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": message}),
        }

    result = {"job_id": job_id}
    return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}


def download_file_from_url(source_url):
    """Downloads file from the source URL and returns its content."""
    result = {}
    try:
        response = requests.get(source_url)
        response.raise_for_status()
        result["content"] = response.content
    except requests.RequestException as e:
        msg = f"Error downloading file from {source_url}: {str(e)}"
        logger.error(msg)
        raise Exception(msg) from e

    content_type = None

    # Try to get the content type from the HTTP response headers
    if source_url:
        response = requests.head(source_url)  # Perform a HEAD request to get headers
        content_type = response.headers.get("Content-Type")
        logger.info(f"Read content_type={content_type} from headers")
    
    # infer it based on the file extension
    if not content_type:
        fname = source_url.split("?")[0].rsplit("/", 1)[1]
        guessed_type, _ = mimetypes.guess_type(fname)
        content_type = guessed_type if guessed_type else "application/octet-stream"
        logger.info(f"Inferred content_type={content_type} from filename")
    result["content_type"] = content_type
    return result
    

def upload_file_to_s3(bucket_name, object_key, file_content, content_type):
    """Uploads the file content to the specified S3 bucket."""
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=file_content,
            ContentType=content_type  # Set the content type here
        )
        logger.info(f"File successfully uploaded to s3://{bucket_name}/{object_key}")
    except ClientError as e:
        logger.error(
            f"Error uploading file to s3://{bucket_name}/{object_key}: "
            + f"{e.response['Error']['Message']}"
        )
        raise


def create_job(job_id, bucket_name, object_key, metadata=None):
    s3_url = f"s3://{bucket_name}/{object_key}"
    try:
        item = {
            "job_id": job_id,
            "created_at": datetime.utcnow().isoformat(),
            "url": s3_url,
            "status": "started",
            "ttl": int(time.time()) + (TTL_DAYS * 24 * 60 * 60),
        }

        if metadata:
            item["metadata"] = metadata

        _ = TABLE.put_item(Item=item)
        logger.info(f"Job {job_id} created successfully")
    except ClientError as e:
        msg = f"Error creating job {job_id} record: {e.response['Error']['Message']}"
        logger.error(msg)
        raise


def update_job(job_id, status, urls=None, message=None, metadata=None):
    try:
        item = {
            "job_id": job_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": status,
            "ttl": int(time.time()) + (TTL_DAYS * 24 * 60 * 60),
        }

        if status == "success" and urls:
            item["urls"] = urls
        elif message:
            item["message"] = message

        if metadata:
            item["metadata"] = metadata

        _ = TABLE.put_item(Item=item)
        logger.info(f"Job {job_id} with status={status!r} updated successfully")
    except ClientError as e:
        msg = f"Error updating job {job_id}: {e.response['Error']['Message']}"
        logger.error(msg)
        raise
