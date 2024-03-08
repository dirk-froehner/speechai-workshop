# Account preparation "service"

This stack prepares a fresh AWS account for the following:
* Enable API Gateway to log incoming requests to CloudWatch Logs. See: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-account.html

## Prerequisites

For deployments, an Amazon S3 bucket is required for the packaged AWS SAM app and the transformed AWS CloudFormation template. The `sam deploy` command creates that bucket automatically, but unfortunately only in interactive mode (`--guided`). Hence, a respective bucket needs to be created upfront and passed to the SAM command.

```bash
aws s3 mb s3://<aws-account-id>-<aws-region>-sam-cli-source-bucket --profile <profile> --region <aws-region>
```

## Deployment

Without further interaction, the following command deploys the stack.

Note: Since the CloudFormation template aims to create a named role, we need to `--capabilities CAPABILITY_NAMED_IAM` in the arguments.

```bash
export SAM_BUCKET_NAME=<name of the S3 bucket created in 0-account-preparation>
export SAM_AWS_PROFILE=<associated AWS access key from .aws/credentials>
export SAM_AWS_REGION=<region where you want deploy your stack>
export SAM_STAGE=<stage>

sam deploy --debug --stack-name $SAM_STAGE-eecc-auxs-acct --capabilities CAPABILITY_NAMED_IAM --s3-bucket $SAM_BUCKET_NAME --profile $SAM_AWS_PROFILE --region $SAM_AWS_REGION --tags Stage=$SAM_STAGE Workload=eecc Context=auxs Service=acct WorkloadLongName=elfish-electrons-customer-care ContextLongName=auxiliary-service ServiceLongName=account-preparation

```
