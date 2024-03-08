#!/bin/bash

# The environment variables below should bet set already externally.

# Echo environment variables.
echo "Environment variables:"
echo "AWS account details:"
echo "SAM_AWS_ACCOUNT_ID = "$SAM_AWS_ACCOUNT_ID
echo "SAM_AWS_REGION     = "$SAM_AWS_REGION
echo "SAM_AWS_PROFILE    = "$SAM_AWS_PROFILE
echo "SAM_STAGE          = "$SAM_STAGE
echo "SAM_BUCKET_NAME    = "$SAM_BUCKET_NAME
echo "Workload details:"
echo "SAM_WORKLOAD       = "$SAM_WORKLOAD
echo "SAM_WORKLOAD_LONG  = "$SAM_WORKLOAD_LONG

# Environment variables specific to this service.
export SAM_CONTEXT=boff
export SAM_SERVICE=dins
export SAM_CONTEXT_LONG=backoffice-services
export SAM_SERVICE_LONG=datalake-ingestion-service

# Echo environment variables specific to this service.
echo "Service details:"
echo "SAM_CONTEXT        = "$SAM_CONTEXT
echo "SAM_SERVICE        = "$SAM_SERVICE
echo "SAM_CONTEXT_LONG   = "$SAM_CONTEXT_LONG
echo "SAM_SERVICE_LONG   = "$SAM_SERVICE_LONG

sam deploy --debug --stack-name $SAM_STAGE-$SAM_WORKLOAD-$SAM_CONTEXT-$SAM_SERVICE --capabilities CAPABILITY_IAM --s3-bucket $SAM_BUCKET_NAME --profile $SAM_AWS_PROFILE --region $SAM_AWS_REGION --parameter-overrides ParameterKey=Stage,ParameterValue=$SAM_STAGE ParameterKey=Workload,ParameterValue=$SAM_WORKLOAD ParameterKey=Context,ParameterValue=$SAM_CONTEXT ParameterKey=Service,ParameterValue=$SAM_SERVICE ParameterKey=WorkloadLongName,ParameterValue=$SAM_WORKLOAD_LONG ParameterKey=ContextLongName,ParameterValue=$SAM_CONTEXT_LONG ParameterKey=ServiceLongName,ParameterValue=$SAM_SERVICE_LONG --tags Stage=$SAM_STAGE Workload=$SAM_WORKLOAD Context=$SAM_CONTEXT Service=$SAM_SERVICE WorkloadLongName=$SAM_WORKLOAD_LONG ContextLongName=$SAM_CONTEXT_LONG ServiceLongName=$SAM_SERVICE_LONG
