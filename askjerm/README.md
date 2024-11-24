# AskJerm demo using Amazon Bedrock

Interview my AI agent!

AskJerm is a Generative AI implementation using [AWS Bedrock][Bedrock]. It uses a
[RAG (Response-Augmented Generation)][RAG] pipeline to combine queries withknowledge
bases that have been ingested and stored in a vector database. The "augmented" query is
then sent to the [Anthropic Claude v2][Claude] foundational model.

Knowledge Bases used:
- [The text of my resume](data/Schaub_CV_2024-11-full.txt) uploaded to an S3 bucket
- [The content of my website](https://jeremyschaub.us/) using a web crawler
- some papers and publications that I have written (TODO)

## Code
- [simple conversing with foundational model](src/simple_converse.py) (No knowledge bases)
- [simple invoking an agent](src/simple_agent.py)


## Setup
### Requesting model access
1. Request access to foundational model (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
2. *Important* request access to embeddings model (`amazon.titan-embed-text-v2:0`)

### Creating the knowledge base
1. Create an S3 bucket and upload the input document(s)
2. From the [AWS Bedrock console][Console] -> Knowledge Bases, create a knowledge base from the S3 bucket with default settings
3. Sync the knowledge base (make sure you have requested access to both the foundational model and the embeddings model)

## Testing the Knowledge bases
After creating and syncing the knowledge bases, I asked questions that can only
be answered using the knowledge bases.

For example, my education level is listed in the text of my resume:

![Resume test](img/bedrock_test.png)

To test the web crawler, I asked a question about a [disaster recovery blog post][DR]
from my site.

![Web crawler test](img/bedrock_dr_test.png)

[Bedrock]: https://aws.amazon.com/bedrock/
[RAG]: https://aws.amazon.com/what-is/retrieval-augmented-generation/
[Claude]: https://www.anthropic.com/news/claude-2
[Console]: https://console.aws.amazon.com/bedrock/
[DR]: https://jeremyschaub.us/posts/post013-issi-dr/index.html
