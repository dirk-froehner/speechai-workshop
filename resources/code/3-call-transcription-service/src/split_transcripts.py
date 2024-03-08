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
import json
import boto3
import aux
import aux_eventbridge_events

# ---------------------------------------------------------------------------------------------------------------------
# Globals.
# ---------------------------------------------------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

s3_client = boto3.client('s3')

ENV_DATA_LAKE_DATA_BUCKET_ARN  = "DATA_LAKE_DATA_BUCKET_ARN"
ENV_DATA_LAKE_DATA_BUCKET_NAME = "DATA_LAKE_DATA_BUCKET_NAME"
ENV_DATA_ACCESS_ROLE_ARN = "DATA_ACCESS_ROLE_ARN"

def construct_destination_object_keys(logger, source_object_key):
    """
    Determine the destination object key based on the source object key.
    """
    logger.debug("Create the destination object key, based on the source object key:")
    logger.debug("source_object_key: %s", source_object_key)
    destination_object_key = source_object_key
    # Replace "raw" with "prepared".
    destination_object_key = destination_object_key.replace("/raw/", "/consumable/")
    # Replace "_call-analytics.json" with "_transcript_agent.txt" and "_transcript_customer.txt"
    destination_object_key_agent = destination_object_key.replace(
        "_call-analytics.json", "_transcript_agent.txt"
    )
    destination_object_key_customer = destination_object_key.replace(
        "_call-analytics.json", "_transcript_customer.txt"
    )
    destination_object_keys = {
        "agent": destination_object_key_agent,
        "customer": destination_object_key_customer
    }
    logger.debug("destination_object_keys: %s", destination_object_keys)
    return destination_object_keys


def split_transcript(logger, source_bucket_name, source_object_key, destination_bucket_name, destination_object_keys):

    logger.debug("Read complete raw call analytics from %s.", "s3://" + source_bucket_name + "/" + source_object_key)
    # Read raw call analytics response.
    response = s3_client.get_object(
        Bucket=source_bucket_name,
        Key=source_object_key
    )
    content = response['Body'].read().decode('utf-8')
    agent = ""
    customer = ""

    #convert string back into json
    contentJson = json.loads(content)
    #concatenate transcript per agent/customer
    for x in contentJson['Transcript']:
        if x["ParticipantRole"] == "AGENT":
            agent +=x["Content"] +" "
        else:
            customer += x["Content"] + " "

    logger.debug("Agent text: %s", agent)
    logger.debug("Customer text: %s", customer)

    #Write separate transcripts back into S3 bucket
    s3_client.put_object(
        Body=agent,
        Bucket=destination_bucket_name,
        Key=destination_object_keys["agent"]
    )

    s3_client.put_object(
        Body=customer,
        Bucket=destination_bucket_name,
        Key=destination_object_keys["customer"]
    )


# --------------------------------------------------------------------------------------------------
# Lambda handler.
# --------------------------------------------------------------------------------------------------

def lambda_handler(event, context):

    # If the environment advises on a specific debug level, set it accordingly.
    aux.update_log_level(LOGGER, event, context)
    # Log environment details.
    aux.log_env_details(LOGGER)
    # Log request details.
    aux.log_event_and_context(LOGGER, event, context)

    source_bucket_name = aux_eventbridge_events.extract_source_bucket_name(LOGGER, event)
    source_object_key = aux_eventbridge_events.extract_source_object_key(LOGGER, event)
    # Extract destination bucket name from environment variable.
    destination_bucket_name = os.environ.get(ENV_DATA_LAKE_DATA_BUCKET_NAME)
    # Construct destination object key based on source object key.
    destination_object_keys = construct_destination_object_keys(LOGGER, source_object_key)

    #Invoke split transcripts function
    split_transcript(LOGGER, source_bucket_name, source_object_key, destination_bucket_name, destination_object_keys)

# --------------------------------------------------------------------------------------------------
