# AskJerm demo using Amazon Bedrock

Interview my AI agent!

AskJerm is a Generative AI implementation using [AWS Bedrock][Bedrock]. It uses a
[RAG (Response-Augmented Generation)][RAG] pipeline to combine queries withknowledge
bases that have been ingested and stored in a vector database. The "augmented" query is
then sent to the [Anthropic Claude v2][Claude] foundational model.

Knowledge Bases used:
- [The text of my resume](data/Schaub_CV_2024-11-full.txt) uploaded to an S3 bucket
- [My  website](https://jeremyschaub.us/about.html) using a web crawler
- some papers and publications that I have written (TODO)

## Code
- [simple conversing with foundational model](src/simple_converse.py) (No knowledge bases)


## Setup
### Requesting model access
1. Request access to foundational model ()
2. *Important* request access to embeddings model (amazon.titan-embed-text-v2:0)

### Creating the knowledge base
1. Select input document(s)
2. Create an S3 bucket
3. Upload the input document(s)
4. In Amazon Bedrock -> Knowledge Bases, create a knowledge base from the S3 bucket with default settings
5. Sync the knowledge base (make sure you have requested access to both the foundational model and the embeddings model)

After completing these steps, you can use the Bedrock Knowledge Base console
to select the foundational model, and ask a question that can only be answered from
the knowledge base:
![Console test](img/bedrock_test.png)

[Bedrock]: https://aws.amazon.com/bedrock/
[RAG]: https://aws.amazon.com/what-is/retrieval-augmented-generation/
[Claude]: https://www.anthropic.com/news/claude-2
