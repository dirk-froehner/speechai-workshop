#!/bin/bash

echo "--------------------------------------------------------------------------------"
echo "Deploying Speech AI workshop services"
echo "--------------------------------------------------------------------------------"

# Evaluate command line args.
DEF_ALL="all"
DEF_EE="ee"
MODE=""

if [ $# -ne 1 ]; then
    echo "You have to provide either '$DEF_ALL' or '$DEF_EE' as command line argument."
    echo "'all' means that all services are deployed and you use that when you bring your own AWS account."
    echo "'ee' means you're on an AWS event and AWS provides accounts."
    exit 0
fi

if [ "$1" = "$DEF_ALL" ]; then
    echo "In own-account mode."
    MODE=$DEF_ALL
elif [ "$1" = "$DEF_EE" ]; then
    echo "In EventEngine mode."
    MODE=$DEF_EE
else
    echo "Unknown parameter $1"
    exit 0
fi

# Prepare AWS account details.
echo "--------------------------------------------------------------------------------"
echo "Fetching AWS account details"
echo "--------------------------------------------------------------------------------"
source "./my-aws-account-details.sh"
echo "AWS account details:"
echo "SAM_AWS_ACCOUNT_ID = "$SAM_AWS_ACCOUNT_ID
echo "SAM_AWS_REGION     = "$SAM_AWS_REGION
echo "SAM_AWS_PROFILE    = "$SAM_AWS_PROFILE
echo "SAM_STAGE          = "$SAM_STAGE
echo "SAM_BUCKET_NAME    = "$SAM_BUCKET_NAME

# Create artifact bucket for SAM.
aws s3 mb s3://$SAM_BUCKET_NAME --profile $SAM_AWS_PROFILE --region $SAM_AWS_REGION

# Prepare workload details.
export SAM_WORKLOAD=eecc
export SAM_WORKLOAD_LONG=elvish-electrons-customer-care
echo "Workload details:"
echo "SAM_WORKLOAD       = "$SAM_WORKLOAD
echo "SAM_WORKLOAD_LONG  = "$SAM_WORKLOAD_LONG

# Execute deploy.sh for each service context.
if [ "$MODE" = "$DEF_ALL" ]; then
    echo "--------------------------------------------------------------------------------"
    echo "Deploying service 0-account-preparation"
    echo "--------------------------------------------------------------------------------"
    cd "0-account-preparation"
    source "./deploy.sh"
    cd ../
else
    echo "--------------------------------------------------------------------------------"
    echo "Skipping service 0-account-preparation"
    echo "--------------------------------------------------------------------------------"
fi

if [ "$MODE" = "$DEF_ALL" ]; then
    echo "--------------------------------------------------------------------------------"
    echo "Deploying service 1-application-preparation"
    echo "--------------------------------------------------------------------------------"
    cd "1-application-preparation"
    source "./deploy.sh"
    cd ../
else
    echo "--------------------------------------------------------------------------------"
    echo "Skipping service 1-application-preparation"
    echo "--------------------------------------------------------------------------------"
fi

echo "--------------------------------------------------------------------------------"
echo "Deploying service 2-datalake-ingestion-service"
echo "--------------------------------------------------------------------------------"
cd "2-datalake-ingestion-service"
source "./deploy.sh"
cd ../

echo "--------------------------------------------------------------------------------"
echo "Deploying service 3-call-transcription-service"
echo "--------------------------------------------------------------------------------"
cd "3-call-transcription-service"
source "./deploy.sh"
cd ../

echo "--------------------------------------------------------------------------------"
echo "Deploying service 4-call-comprehension-service"
echo "--------------------------------------------------------------------------------"
cd "4-call-comprehension-service"
source "./deploy.sh"
cd ../

# Done.
echo "--------------------------------------------------------------------------------"
echo "All done"
echo "--------------------------------------------------------------------------------"
