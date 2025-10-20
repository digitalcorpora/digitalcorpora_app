[![codecov](https://codecov.io/gh/digitalcorpora/digitalcorpora_app/branch/bottle-main/graph/badge.svg?token=E6GE1KIGAT)](https://app.codecov.io/gh/digitalcorpora/digitalcorpora_app/tree/bottle-main)

# digitalcorpora.org python app
This repo provides the custom-written Python code for the https://DigitalCorpora.org/ website.

The website runs with WordPress. This repo runs the API and S3 browser functionality at https://api.digitalcorpora.org/. The development and production API endpoints are now managed via AWS SAM and API Gateway, with custom domains (e.g., api.digitalcorpora.org, search.digitalcorpora.org, app.digitalcorpora.org) all pointing to the same deployment.

The repo is designed to be checked out anywhere for local development. It runs the python application in Bottle/Flask for local testing, and is deployed to AWS Lambda via AWS SAM for production. You can also modify the config file to browse other S3 buckets, should you wish to use this on another website.

# To setup
1. Install dependencies (see below)
2. Update the AWS SAM template (template.yaml) with your custom domain, ACM certificate ARN (from us-west-2), and (optionally) Route53 Hosted Zone ID if you use Route53 (not required for most users).
3. Deploy using AWS SAM (see Makefile or deployment instructions below).
4. Create a certificate for your subdomain (e.g., api.digitalcorpora.org) in AWS Certificate Manager (ACM) in us-west-2.
5. Add the required CNAME record to your DNS provider to validate the certificate.
6. Create a CNAME in your DNS provider pointing your subdomain (e.g., api.digitalcorpora.org) to the API Gateway custom domain target (see AWS Console for the correct value).

# aws deployment
- We use AWS SAM for deployment to AWS Lambda and API Gateway.
- MySQL database credentials are stored in AWS Secrets Manager.
- Lambda needs to be given access to the secrets manager. See:
  - https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html
  - https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_examples.html#auth-and-access_examples_read
  - https://docs.aws.amazon.com/secretsmanager/latest/userguide/troubleshoot_rotation.html

- The canonical API endpoint is now https://api.digitalcorpora.org/ (or your chosen custom domain).

# Other options
# - aws challice - completely different thing. new decorators
# - See AWS SAM documentation for advanced deployment options.
