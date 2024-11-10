# Send email via API Gateway and AWS Simple Email Service (SES)

This is an AWS Serverless Application Model (SAM) template that creates an
API Gateway endpoint with a Lambda function that invokes the Simple Email Service.

SES must be setup manually with a verified email for the Lambda function to work
correctly. Edit `samconfig.toml` and add this email as the `DeliverToEmail`.

In the [lambda function][src/send_to_ses/app.py], the email source and destination are
set to this same verified email address.

```sh
sam build
sam deploy --guided
```
