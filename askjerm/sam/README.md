# Serverless Application Model (SAM) template for AskJerm

Currently, [this template](template.yml) only contains the API Gateway endpoint
and [this Lambda function](src/invoke_agent/app.py) to invoke the agent.

## Deploy
```sh
sam validate --lint
sam build
sam deploy --guided
```

## Test from command line
```bash
curl -X POST "$URL" --header 'Content-Type: application/json' --data '{"inputTxt": "Tell Me about Jeremy"}'
```
