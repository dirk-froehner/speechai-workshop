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
import uuid
import urllib.parse
import boto3
import aux
import aux_paths
import aux_lambda_events

# ---------------------------------------------------------------------------------------------------------------------
# Globals.
# ---------------------------------------------------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

TRANSCRIBE_CLIENT = boto3.client("transcribe")

ENV_RAW_DATA_BUCKET_ARN  = "RAW_DATA_BUCKET_ARN"
ENV_RAW_DATA_BUCKET_NAME = "RAW_DATA_BUCKET_NAME"
ENV_PREPARED_DATA_BUCKET_ARN  = "PREPARED_DATA_BUCKET_ARN"
ENV_PREPARED_DATA_BUCKET_NAME = "PREPARED_DATA_BUCKET_NAME"

# ---------------------------------------------------------------------------------------------------------------------
# Transcribe S3 objects mentioned in S3 events to a destination folder with specific key prefix.
# ---------------------------------------------------------------------------------------------------------------------

def is_relevant_s3_event(s3_event):
    if (s3_event.is_event_source_s3 and s3_event.is_object_created_put and
        os.environ.get(ENV_RAW_DATA_BUCKET_NAME) == s3_event.get_bucket_name() and
        s3_event.get_object_key().startswith(aux_paths.PATH_COMMON_PREFIX + aux_paths.PATH_RAW_AUDIO_FROM_CONNECT)
    ):
        return True
    else:
        return False


def create_destination_bucket_name():
    return os.environ.get(ENV_RAW_DATA_BUCKET_NAME)


def create_destination_object_key(source_object_key):
    LOGGER.debug("Create the destination object key, based on the source object key:")
    # Source object key example: contact-center/call-recordings/raw-audio-from-connect/2022/03/24/8e1ed52f-63d5-45de-bf9d-8c54c4c64231_2022-03-24T12%3A43%3A00Z.wav
    LOGGER.debug("source_object_key: %s", source_object_key)
    # Cut off the prefix "contact-center/call-recordings/raw-audio-from-connect/" from source_object_key.
    index = len(aux_paths.PATH_COMMON_PREFIX + aux_paths.PATH_RAW_AUDIO_FROM_CONNECT)
    destination_object_key = source_object_key[index:]
    LOGGER.debug("Step 1: %s", destination_object_key)
    # Add the specific prefix to the destination object key.
    destination_object_key = aux_paths.PATH_COMMON_PREFIX + aux_paths.PATH_RAW_RESPONSE_FROM_TRANSCRIBE + destination_object_key
    LOGGER.debug("Step 2: %s", destination_object_key)
    destination_object_key = destination_object_key.replace(".wav", aux_paths.PATH_TRANSCRIPTION_RESULT + ".json")
    LOGGER.debug("Step 3: %s", destination_object_key)
    return destination_object_key


def transcribe_call_recordings(s3_events):
    LOGGER.debug("Transcribe relevant objects mentioned in S3 events and store transcripts in destination bucket.")
    for s3_event in s3_events:
        LOGGER.debug("Looking into s3 event: %s", s3_event.get_single_s3_event())
        # Check if the S3 event is relevant for call-recording ingestion.
        if (is_relevant_s3_event(s3_event)):
            LOGGER.debug("Single S3 event is relevant for call-recording transcription.")
            LOGGER.debug("Transcribe call-recording S3 object with the following specs:")
            # Assemble source information.
            source_bucket_name = s3_event.get_bucket_name()
            LOGGER.debug("source_bucket_name: %s", source_bucket_name)
            source_object_key = s3_event.get_object_key()
            # The object key is URL-encoded in the S3 event, so we have to decode it for the copy operation later!
            unquoted_source_object_key = urllib.parse.unquote_plus(source_object_key)
            LOGGER.debug("source_object_key: %s", source_object_key)
            LOGGER.debug("unquoted_source_object_key: %s", unquoted_source_object_key)
            # The resulting S3 URI of the media object.
            media_uri = "s3://" + source_bucket_name + "/" + unquoted_source_object_key
            LOGGER.debug("S3 URI for the media object: %s", media_uri)

            # Assemble destination information.
            destination_bucket_name = create_destination_bucket_name()
            LOGGER.debug("destination_bucket_name: %s", destination_bucket_name)
            destination_object_key = create_destination_object_key(unquoted_source_object_key)
            LOGGER.debug("destination_object_key: %s", destination_object_key)
            # The transcription job doesn't allow colons in the destination object key, so we need to kill them.
            cleansed_destination_object_key = aux_paths.PATH_RENAME_ME + destination_object_key.replace(":", "")
            LOGGER.debug("cleansed_destination_object_key: %s", cleansed_destination_object_key)

            # Transcribe job name.
            job_name = "job-" + uuid.uuid4().hex

            # Invoke Transcribe-API.
            response = TRANSCRIBE_CLIENT.start_transcription_job(
                LanguageCode         = "en-US",
                Media                = {"MediaFileUri": media_uri},
                MediaFormat          = "wav",
                OutputBucketName     = destination_bucket_name,
                OutputKey            = cleansed_destination_object_key,
                TranscriptionJobName = job_name,
                Settings = {
                   'ChannelIdentification': True,
                }
            )
            LOGGER.debug("Response: %s", response)
        else:
            LOGGER.debug("Single S3 event is not relevant for call-recording ingestion.")

# ---------------------------------------------------------------------------------------------------------------------
# Lambda handler.
# ---------------------------------------------------------------------------------------------------------------------

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

    # Specifically for this Lambda function: copy S3 objects mentioned in the S3 events to a destination bucket.
    destination_bucket_name = os.environ.get(ENV_PREPARED_DATA_BUCKET_NAME)
    # Also, add a specific prefix to the destination object key.
    transcribe_call_recordings(s3_events)

# ---------------------------------------------------------------------------------------------------------------------
