# SAM Testing Setup for DigitalCorpora App

This document explains how to deploy the DigitalCorpora application for testing using AWS SAM (Serverless Application Model) on an ad-hoc domain.

## Prerequisites

1. **AWS CLI** installed and configured
2. **SAM CLI** installed (`pip install aws-sam-cli`)
3. **AWS credentials** configured with appropriate permissions
4. **SSL Certificate** in AWS Certificate Manager for your test domain
5. **Route53 Hosted Zone** for your test domain

## Configuration

### 1. Update samconfig.toml

The `samconfig.toml` file has been updated with a new `[test]` profile that uses:
- Stack name: `digitalcorpora-app-test`
- Domain: `test.digitalcorpora.org`
- Region: `us-west-2`

### 2. Update template.yaml

Before deploying, you need to update the following parameters in `template.yaml`:

```yaml
Parameters:
  CertificateArn:
    Default: "arn:aws:acm:us-west-2:YOUR-ACCOUNT-ID:certificate/YOUR-CERTIFICATE-ID"

  HostedZoneId:
    Default: "YOUR-HOSTED-ZONE-ID"
```

Replace:
- `YOUR-ACCOUNT-ID` with your AWS account ID
- `YOUR-CERTIFICATE-ID` with your ACM certificate ID
- `YOUR-HOSTED-ZONE-ID` with your Route53 hosted zone ID

## Deployment

### Quick Deployment

Use the provided script:
```bash
./deploy_test.sh
```

### Manual Deployment

1. **Build the application:**
   ```bash
   sam build --profile test
   ```

2. **Deploy to AWS:**
   ```bash
   sam deploy --profile test
   ```

3. **Monitor deployment:**
   ```bash
   aws cloudformation describe-stacks --stack-name digitalcorpora-app-test --region us-west-2
   ```

## Testing

Once deployed, your application will be available at:
- **URL**: https://test.digitalcorpora.org
- **API Gateway URL**: Available in the CloudFormation outputs

### Test Endpoints

- `/` - Main page
- `/ver` - Version information
- `/reports` - Reports page
- `/corpora/` - S3 bucket browser
- `/downloads/` - Downloads browser

## Cleanup

When you're done testing, delete the stack:

```bash
sam delete --profile test
```

## Troubleshooting

### Common Issues

1. **Certificate not found**: Ensure your SSL certificate is in the correct region (us-west-2)
2. **Hosted zone not found**: Verify your Route53 hosted zone exists
3. **Permission denied**: Check your AWS credentials and IAM permissions
4. **Build failures**: Ensure all dependencies are in `requirements.txt`

### Logs

View Lambda function logs:
```bash
sam logs -n DigitalCorporaFunction --profile test --tail
```

### Local Testing

Test locally before deploying:
```bash
sam local start-api --profile test
```

## Architecture

The SAM deployment creates:
- **Lambda Function**: Runs your Bottle application
- **API Gateway**: Handles HTTP requests and routing
- **Custom Domain**: Maps your test domain to the API
- **Route53 Record**: DNS record for the custom domain
- **IAM Roles**: Permissions for S3 access and logging

## Environment Variables

The Lambda function is configured with:
- `PYTHONPATH`: `/var/task`
- `TEMPLATE_DIR`: `/var/task/templates`
- `STATIC_DIR`: `/var/task/static`

## Security

- The Lambda function has read-only access to the `digitalcorpora` S3 bucket
- All traffic is served over HTTPS
- API Gateway handles authentication and rate limiting