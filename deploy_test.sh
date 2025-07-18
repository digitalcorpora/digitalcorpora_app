#!/bin/bash

# Deploy DigitalCorpora App for Testing
# This script deploys the application using the 'test' profile in samconfig.toml

set -e

echo "=== DigitalCorpora App Test Deployment ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI not found. Please install it first:"
    echo "   pip install aws-sam-cli"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Validate SAM template
echo "Validating SAM template..."
if ! sam validate --profile test; then
    echo "❌ SAM template validation failed"
    exit 1
fi
echo "✅ SAM template validation passed"
echo ""

# Build the application
echo "Building DigitalCorpora App for testing..."
if ! sam build --profile test; then
    echo "❌ SAM build failed"
    exit 1
fi
echo "✅ SAM build completed"
echo ""

# Deploy to test environment
echo "Deploying to test environment..."
if ! sam deploy --profile test; then
    echo "❌ SAM deployment failed"
    exit 1
fi
echo "✅ SAM deployment completed"
echo ""

# Get deployment outputs
echo "Getting deployment outputs..."
STACK_NAME=$(sam list --profile test | grep digitalcorpora-app-test | awk '{print $1}')
if [ -z "$STACK_NAME" ]; then
    echo "❌ Could not find deployed stack"
    exit 1
fi

API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region us-west-2 --query 'Stacks[0].Outputs[?OutputKey==`DigitalCorporaApi`].OutputValue' --output text)
CUSTOM_DOMAIN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region us-west-2 --query 'Stacks[0].Outputs[?OutputKey==`CustomDomainUrl`].OutputValue' --output text)

echo "✅ Deployment successful!"
echo ""
echo "=== Deployment Information ==="
echo "Stack Name: $STACK_NAME"
echo "API Gateway URL: $API_URL"
echo "Custom Domain: $CUSTOM_DOMAIN"
echo ""
echo "=== Test Endpoints ==="
echo "API Gateway: $API_URL"
echo "Custom Domain: $CUSTOM_DOMAIN"
echo ""
echo "=== Available Routes ==="
echo "- / (Main page)"
echo "- /ver (Version info)"
echo "- /reports (Reports page)"
echo "- /corpora/ (S3 bucket browser)"
echo "- /downloads/ (Downloads browser)"
echo "- /search (Search interface)"
echo ""
echo "=== Useful Commands ==="
echo "View logs: sam logs -n DigitalCorporaFunction --profile test --tail"
echo "Delete stack: sam delete --profile test"
echo "Local testing: sam local start-api --profile test"