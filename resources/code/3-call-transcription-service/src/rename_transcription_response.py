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

from operator import truediv
import os
import logging
import urllib.parse
import boto3
import aux
import aux_paths
import aux_lambda_events

# --------------------------------------------------------------------------------------------------
# Globals.
# --------------------------------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

S3_CLIENT = boto3.client("s3")

ENV_RAW_DATA_BUCKET_ARN  = "RAW_DATA_BUCKET_ARN"
ENV_RAW_DATA_BUCKET_NAME = "RAW_DATA_BUCKET_NAME"
ENV_DATA_ACCESS_ROLE_ARN = "DATA_ACCESS_ROLE_ARN"

# --------------------------------------------------------------------------------------------------
# Rename the result from a transcription job that has no colons in the time stamp.
# --------------------------------------------------------------------------------------------------

def is_relevant_s3_event(s3_event):
    if (s3_event.is_event_source_s3 and s3_event.is_object_created_put and
        os.environ.get(ENV_RAW_DATA_BUCKET_NAME) == s3_event.get_bucket_name() and
        s3_event.get_object_key().startswith(
            aux_paths.PATH_COMMON_PREFIX + aux_paths.PATH_RAW_RESPONSE_FROM_TRANSCRIBE
        ) and
        aux_paths.PATH_TRANSCRIPTION_RESULT in s3_event.get_object_key() and
        s3_event.get_object_key().endswith(aux_paths.PATH_RENAME_ME)
    ):
        return True
    else:
        return False


def create_destination_bucket_name():
    return os.environ.get(ENV_RAW_DATA_BUCKET_NAME)


def create_destination_object_key(source_object_key):
    LOGGER.debug("Create the destination object key, based on the source object key:")
    # Source object key example: 
    # contact-center/call-recordings/raw-response-from-transcribe/2022/03/24/8e1ed52f-63d5-45de-bf9d-8c54c4c64231_2022-03-24T125100Z_transcription-response.json
    # contact-center/call-recordings/raw-response-from-transcribe/2022/03/24/8e1ed52f-63d5-45de-bf9d-8c54c4c64231_2022-03-24T125100Z_transcription-response.json
    # Would lead to this result: 8e1ed52f-63d5-45de-bf9d-8c54c4c64231_2022-03-24T12:51:00Z_transcription-response.json
    LOGGER.debug("source_object_key: %s", source_object_key)
    # Just blindly insert those colons.
    destination_object_key = source_object_key[:121]
    LOGGER.debug("destination_object_key: %s", destination_object_key)
    destination_object_key = destination_object_key + ":"
    LOGGER.debug("destination_object_key: %s", destination_object_key)
    destination_object_key = destination_object_key + source_object_key[121:123]
    LOGGER.debug("destination_object_key: %s", destination_object_key)
    destination_object_key = destination_object_key + ":"
    LOGGER.debug("destination_object_key: %s", destination_object_key)
    destination_object_key = destination_object_key + source_object_key[123:]
    LOGGER.debug("destination_object_key: %s", destination_object_key)
    destination_object_key = destination_object_key.replace(aux_paths.PATH_RENAME_ME, "")
    LOGGER.debug("destination_object_key: %s", destination_object_key)
    return destination_object_key


def rename_transcription_response(s3_events):
    LOGGER.debug("Rename the result from a transcription job that has no colons in the time stamp.")
    for s3_event in s3_events:
        LOGGER.debug("Looking into single S3 event: %s", s3_event.get_single_s3_event())
        # Check if the S3 event is relevant for call-recording ingestion.
        if (is_relevant_s3_event(s3_event)):
            LOGGER.debug("Single S3 event is relevant for renaming.")
            LOGGER.debug("Rename transcription response:")
            # Assemble source information.
            source_bucket_name = s3_event.get_bucket_name()
            LOGGER.debug("source_bucket_name: %s", source_bucket_name)
            source_object_key = s3_event.get_object_key()
            # The object key is URL-encoded in the S3 event, so we have to decode it for the copy operation later!
            unquoted_source_object_key = urllib.parse.unquote_plus(source_object_key)
            LOGGER.debug("source_object_key: %s", source_object_key)
            LOGGER.debug("unquoted_source_object_key: %s", unquoted_source_object_key)

            # Assemble output location.
            destination_bucket_name = create_destination_bucket_name()
            LOGGER.debug("destination_bucket_name: %s", destination_bucket_name)
            destination_object_key = create_destination_object_key(unquoted_source_object_key)
            LOGGER.debug("destination_object_key: %s", destination_object_key)

            LOGGER.debug("Copy the source object into a renamed destination object:")
            copy_source = {'Bucket': source_bucket_name, 'Key': unquoted_source_object_key}
            response = S3_CLIENT.copy_object(
                CopySource = copy_source,
                Bucket = destination_bucket_name,
                Key = destination_object_key)
            LOGGER.debug("Response: %s", response)
            LOGGER.debug("Delete source object with lousy file name:")
            response = S3_CLIENT.delete_object(
                Bucket = source_bucket_name,
                Key = unquoted_source_object_key
            )
            LOGGER.debug("Response: %s", response)
        else:
            LOGGER.debug("Single S3 event is not relevant for renaming.")

# --------------------------------------------------------------------------------------------------
# # Lambda handler.
# --------------------------------------------------------------------------------------------------

def lambda_handler(lambda_event, context):

    # If the environment advises on a specific debug level, set it accordingly.
    aux.update_log_level(LOGGER, lambda_event, context)
    # Log environment details.
    aux.log_env_details(LOGGER)
    # Log request details.
    aux.log_event_and_context(LOGGER, lambda_event, context)

    # Create an object to host all the SNS messages for simple access.
    sns_messages = aux_lambda_events.SnsMessagesWithEmbeddedS3Events(LOGGER, lambda_event)
    # Extract all embedded S3 events from those SNS messages.
    s3_events = sns_messages.get_all_s3_events()

    # Let's go!
    rename_transcription_response(s3_events)

# --------------------------------------------------------------------------------------------------