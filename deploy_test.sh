#!/bin/bash

# Deploy DigitalCorpora App for Testing
# This script deploys the application using the 'test' profile in samconfig.toml

set -e

echo "Building DigitalCorpora App for testing..."
sam build --profile test

echo "Deploying to test environment..."
sam deploy --profile test

echo "Deployment complete!"
echo "Your application should be available at: https://test.digitalcorpora.org"
echo ""
echo "To view the CloudFormation stack:"
echo "aws cloudformation describe-stacks --stack-name digitalcorpora-app-test --region us-west-2"
echo ""
echo "To delete the stack when done testing:"
echo "sam delete --profile test"