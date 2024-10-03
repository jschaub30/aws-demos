#!/bin/bash
set -ex

S3_BUCKET=$(aws cloudformation describe-stacks --region us-east-1 \
  --stack-name convert-demo \
  --query 'Stacks[0].Outputs[?OutputKey==`WebAppBucketName`].OutputValue' \
  --output text)
API_URL=$(aws cloudformation describe-stacks --region us-east-1 \
	--stack-name convert-demo \
	--query "Stacks[0].Outputs[?OutputKey=='ApiGatewayURL'].OutputValue" \
	--output text)
WEB_URL=$(aws cloudformation describe-stacks --region us-east-1 \
	--stack-name convert-demo \
	--query "Stacks[0].Outputs[?OutputKey=='WebAppURL'].OutputValue" \
	--output text)

# Sync the webapp files to the S3 bucket
cat src/webapp/upload_template.js | sed "s|API_GATEWAY_URL|$API_URL|g" >upload.js
aws s3 sync ./src/webapp s3://$S3_BUCKET

echo "Demo deployed to $WEB_URL"
