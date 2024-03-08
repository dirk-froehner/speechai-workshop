# datalake-ingestion-service

Sample service that ingests business events in a data lake.

This service is a sample backoffice service that ingests Lambda events from business services into the raw data tier of a data lake. The Lambda functions in the business services publish their incoming events (that is: the events that trigger their execution) in specific SNS topics. This service chains these SNS topics with Kinesis Firehose delivery streams.

## Parameters

The AWS SAM template for this serverless application comes with the following individual parameters beyond the standard ones (Stage, LogLevel, etc):

```yaml
  # Parameters from AWS SSM Parameter Store for shared resources.

  ApigwRequestEventTopicArn:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "ARN of the shared ApigwRequestEventTopic"
    Default: "/dev/wrb/sns/apigw-request-event-topic/arn"
  ApigwRequestEventTopicName:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "Name of the shared ApigwRequestEventTopic"
    Default: "/dev/wrb/sns/apigw-request-event-topic/name"

  SnsMessageEventTopicArn:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "ARN of the shared SnsMessageEventTopic"
    Default: "/dev/wrb/sns/sns-message-event-topic/arn"
  SnsMessageEventTopicName:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "Name of the shared SnsMessageEventTopic"
    Default: "/dev/wrb/sns/sns-message-event-topic/name"

  SqsMessageEventTopicArn:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "ARN of the shared SqsMessageEventTopic"
    Default: "/dev/wrb/sns/sqs-message-event-topic/arn"
  SqsMessageEventTopicName:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "Name of the shared SqsMessageEventTopic"
    Default: "/dev/wrb/sns/sqs-message-event-topic/name"

  DataLakeRawDataBucketArn:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "ARN of the shared DataLakeRawDataBucket"
    Default: "/dev/wrb/s3/datalake-rawdata-bucket/arn"
  DataLakeRawDataBucketName:
    Type: "AWS::SSM::Parameter::Value<String>"
    Description: "Name of the shared DataLakeRawDataBucket"
    Default: "/dev/wrb/s3/datalake-rawdata-bucket/name"
```

## Deployment

This service tries to create IAM roles with individual names. For that, the `sam deploy` command needs to be invoked with the `--capabilities CAPABILITY_NAMED_IAM` option.

## Patterns

Patterns that are applied in this service:

### Integration patterns

- Message exchange: one-way messaging. This service implements the receiver side.
- Message channels: publish-subscribe messaging. This service implements the subscriber side.
- Message channels: topic-stream-chaining. This service chains SNS topics with Kinesis Firehose delivery streams.

### AWS SAM / CloudFormation patterns

- Best practice: tag all resources. This service tags all resources that are taggable.
- Best practice: control log retention. This service controls individual retention time for CloudWatch Logs log streams.
- Cross-service resources: parameter sharing. This acquires details about shared SNS topics and a shared S3 bucket.
