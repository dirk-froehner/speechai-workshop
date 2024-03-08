# Application preparation "service"

This stack creates shared resources that have no specific service as their owner and shares their details through AWS SSM Parameter Store.

Resources in scope are:
* Amazon S3 bucket for contact-center data (i.e. call recordings). This bucket should be used for configuring an Amazon Connect instance.
* Amazon SNS topic to receive S3 events for new data placed in the above bucket.
* Amazon S3 buckets for all tiers of a data lake (raw, prepared, consumable).
* Amazon SNS topics to receive S3 events for new data placed in any of the data lake buckets.

## Deployment

Without further interaction, the following command deploys the stack:

```bash
export SAM_BUCKET_NAME=<name of the S3 bucket created in 0-account-preparation>
export SAM_AWS_PROFILE=<associated AWS access key from .aws/credentials>
export SAM_AWS_REGION=<region where you want deploy your stack>
export SAM_STAGE=<stage>

sam deploy --debug --stack-name $SAM_STAGE-eecc-auxs-prep --capabilities CAPABILITY_IAM --s3-bucket $SAM_BUCKET_NAME --profile $SAM_AWS_PROFILE --region $SAM_AWS_REGION --tags Stage=$SAM_STAGE Workload=eecc Context=auxs Service=prep WorkloadLongName=elfish-electrons-customer-care ContextLongName=auxiliary-service ServiceLongName=application-preparation
```
