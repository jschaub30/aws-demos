# AskJerm demo using Amazon Bedrock

Interview my AI agent!

AskJerm is a Generative AI implementation using [AWS Bedrock][Bedrock]. The AskJerm
agent invokes a [RAG (Response-Augmented Generation)][RAG] pipeline to combine queries
with knowledge bases that have been ingested and stored in a vector database. The
"augmented" query is then sent to the [Anthropic Claude Haiku v3.5][Claude] foundational model.

Knowledge Bases used:
- [The text of my resume][cv]
- [The content of my website][website] using a web crawler (TODO)

I originally built this using a combination of the AWS Console and some serverless application
model (SAM) scripts, but I then converted it to the [AWS CDK][cdk] so that the manual steps
are replaced with infrastructure as code.

## Cost warning
The default configuration described below results in a cost of approximately $6/day,
primarily from the [Amazon Opensearch Serverless][opensearch] collection in
non-redundant mode. This collection charges 0.5 (ingestion) + 0.5 (search)
OpenSearch Compute Units (OCUs) per day, charged at $0.24/hour.

More details [here][os-pricing].

## Request model access
Before attempting to deploy these stacks, [request access to][model-access]
1. foundational model (`Claude 3.5 Haiku`)
2. embeddings model (`Titan Text Embeddings V2`)


### Install the AWS CDK
See [instructions here][cdk-install].

## Create and deploy the AskJerm agent via the AWS python cdk
This repo creates 2 related stacks via the AWS python cdk:
- AskJermCdkStack: bedrock knowledge base/data source/agent and lambda function to invoke the agent
- StaticWebsiteStack: web client to invoke the lambda function

Code:
- [CDK stack definitions][stack]
- [Lambda function to invoke the agent][lambda]
- [Web app][web]

Do **not** deploy both stacks at once using `cdk deploy --all`, because the static website
must use the Lambda function URL created from the AskJermCdkStack.

```sh
cdk deploy AskJermCdkStack  # wait for this to complete (about 8 minutes)
cdk deploy StaticWebsiteStack  # the lambda function URL will be updated dynamically
```

After deployment, you can invoke the agent via the static website URL that is printed
when the StaticWebsiteStack finishes deploying.

However, the agent doesn't work right away, and I'm still debugging why. I typically
need to sync the data source in the created Knowledge Base via the
[Bedrock console][console], then run some manual tests until it's all working.

### Destroy
```sh
cdk destroy --all
```

## Sources:
- [AWS Labs GenAI CDK](https://github.com/awslabs/generative-ai-cdk-constructs/tree/main/src/cdk-lib/bedrock)

[Bedrock]: https://aws.amazon.com/bedrock/
[cdk]: https://docs.aws.amazon.com/cdk/v2/guide/home.html
[cdk-install]: https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html
[Claude]: https://www.anthropic.com/claude/haiku
[console]: https://console.aws.amazon.com/bedrock/
[cv]: documents/Schaub_CV_2024-11-full.txt
[lambda]: src/lambda.py
[model-access]: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html
[opensearch]: https://aws.amazon.com/opensearch-service/features/serverless/
[os-pricing]: https://aws.amazon.com/opensearch-service/pricing/
[RAG]: https://aws.amazon.com/what-is/retrieval-augmented-generation/
[stack]: askjerm_cdk/askjerm_cdk_stack.py
[web]: src/webapp/index_template.html
[website]: https://jeremyschaub.us/

## Python CDK boilerplate documentation
The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
