# MIT No Attribution
# 
# Copyright 2022 Amazon.com, Inc. or its affiliates
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import logging
import boto3
import aux
import aux_paths
import aux_eventbridge_events

# --------------------------------------------------------------------------------------------------
# Globals.
# --------------------------------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

S3_CLIENT = boto3.client("s3")

ENV_CONTACT_CENTER_DATA_BUCKET_ARN  = "CONTACT_CENTER_DATA_BUCKET_ARN"
ENV_CONTACT_CENTER_DATA_BUCKET_NAME = "CONTACT_CENTER_DATA_BUCKET_NAME"
ENV_DATA_LAKE_DATA_BUCKET_ARN  = "DATA_LAKE_DATA_BUCKET_ARN"
ENV_DATA_LAKE_DATA_BUCKET_NAME = "DATA_LAKE_DATA_BUCKET_NAME"

# --------------------------------------------------------------------------------------------------
# Functions.
# --------------------------------------------------------------------------------------------------

def construct_destination_object_key(logger, source_object_key):
    """
    Based on the object key of the new Amazon Connect call recording, construct the object key for
    ingestion of the new call recording into the data lake bucket.
    """

    # Extract substring of source object key after CallRecordings/
    index = source_object_key.find(aux_paths.PATH_CONNECT_CALLRECORDINGS)
    logger.debug("Index of %s is: %d", aux_paths.PATH_CONNECT_CALLRECORDINGS, index)
    index = index + len(aux_paths.PATH_CONNECT_CALLRECORDINGS)
    logger.debug("Index of next character after %s is: %d",
        aux_paths.PATH_CONNECT_CALLRECORDINGS, index
    )
    tmp_destination_object_key_suffix = source_object_key[index:]
    logger.debug("tmp_destination_object_key_suffix: %s", tmp_destination_object_key_suffix)
    # Reformat the timestamp in the object key, after the call-id.
    destination_object_key_suffix = tmp_destination_object_key_suffix[:52] + "-" + tmp_destination_object_key_suffix[52:54] + "-" + tmp_destination_object_key_suffix[54:62] + ":00Z.wav"
    logger.debug("destination_object_key_suffix: %s", destination_object_key_suffix)
    destination_object_key = aux_paths.PATH_CONNECT_CALLRECORDINGS_RAW + destination_object_key_suffix
    logger.debug("destination_object_key: %s", destination_object_key)
    return destination_object_key

# --------------------------------------------------------------------------------------------------

def lambda_handler(event, context):
    """
    Copy a new call recording from the contact center bucket to the data lake bucket.
    """
    # If the environment advises on a specific debug level, set it accordingly.
    aux.update_log_level(LOGGER, event, context)
    # Log environment details.
    aux.log_env_details(LOGGER)
    # Log request details.
    aux.log_event_and_context(LOGGER, event, context)

    # Extract the AWS account ID where this Lambda function is running.
    aws_account_id = context.invoked_function_arn.split(":")[4]
    LOGGER.debug("aws_account_id: %s", aws_account_id)
    # Extract the AWS region where this Lambda function is running.
    aws_region = os.environ["AWS_REGION"]
    LOGGER.debug("aws_region: %s", aws_region)

    # Extract source bucket name and source object key from EventBridge event.
    copy_source = aux_eventbridge_events.extract_copy_source(LOGGER, event)
    # Extract destination bucket name from environment variable.
    destination_bucket_name = os.environ.get(ENV_DATA_LAKE_DATA_BUCKET_NAME)
    # Construct destination object key based on source object key.
    destination_object_key = construct_destination_object_key(LOGGER, copy_source["Key"])

    # Copy the new call recording from the CC bucket to the DL bucket.
    response = S3_CLIENT.copy_object(
        CopySource = copy_source,
        Bucket = destination_bucket_name,
        Key = destination_object_key
    )
    LOGGER.debug("response: %s", response)

# --------------------------------------------------------------------------------------------------
