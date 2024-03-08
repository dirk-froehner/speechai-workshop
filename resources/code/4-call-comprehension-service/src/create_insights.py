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
import aux_paths

# --------------------------------------------------------------------------------------------------
# Globals.
# --------------------------------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

S3_CLIENT = boto3.client("s3")
COMPREHEND_CLIENT = boto3.client("comprehend")

ENV_DATA_LAKE_DATA_BUCKET_ARN  = "DATA_LAKE_DATA_BUCKET_ARN"
ENV_DATA_LAKE_DATA_BUCKET_NAME = "DATA_LAKE_DATA_BUCKET_NAME"

ENTITY_TYPES = ["COMMERCIAL_ITEM", "DATE", "EVENT", "LOCATION", "ORGANIZATION", "OTHER", "PERSON", "QUANTITY", "TITLE"]

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
    destination_object_key = construct_destination_object_key(LOGGER, source_object_key)

    text, role = load_text_from_s3(source_bucket_name, source_object_key)
    # Also, add a specific prefix to the destination object key.
    result = comprehend_text(text, role)
    # Write insights into S3 bucket.
    write_insights(result, destination_bucket_name, destination_object_key)

# --------------------------------------------------------------------------------------------------

def construct_destination_object_key(logger, source_object_key):
    """
    Determine the destination object key.
    """
    logger.debug("Create the destination object key, based on the source object key.")
    destination_object_key = source_object_key.replace(
        aux_paths.PATH_TRANSCRIBE_CALLANALYTICS_CONSUMABLE,
        aux_paths.PATH_COMPREHEND_INSIGHTS_PREPARED
    )
    logger.debug("destination_object_key step 1: %s", destination_object_key)
    destination_object_key = destination_object_key.replace(
        "transcript", "insights"
    )
    logger.debug("destination_object_key step 2: %s", destination_object_key)
    destination_object_key = destination_object_key.replace(
        ".txt", ".json"
    )
    logger.debug("destination_object_key step 3: %s", destination_object_key)
    return destination_object_key

# --------------------------------------------------------------------------------------------------

def load_text_from_s3(source_bucket_name, source_object_key):
    LOGGER.debug("load_text_from_s3")
    # check if role is customer or agent
    if "agent" in source_object_key:
        role = "agent"
    else:
        role = "customer"
    LOGGER.debug("Read S3 object and make it a JSON object.")
    response = S3_CLIENT.get_object(
        Bucket = source_bucket_name,
        Key    = source_object_key
    )
    LOGGER.debug("response: %s", response)
    object_body = response['Body']
    LOGGER.debug("object_body: %s", object_body)
    full_text = object_body.read()
    LOGGER.debug("full_text (raw): %s", full_text)
    full_text = full_text.decode("utf-8")
    LOGGER.debug("full_text (decoded): %s", full_text)
    return full_text, role

# --------------------------------------------------------------------------------------------------

def comprehend_text(text, role):
    LOGGER.debug("Create insights from text.")
    result = {}
    LOGGER.debug("Text: %s", text)

    # Dominant language.
    dominant_language_response = COMPREHEND_CLIENT.detect_dominant_language(
        Text=text
    )
    LOGGER.debug("Response from detect_dominant_language: %s", json.dumps(dominant_language_response, indent=4))
    # We are only interested in the first element (the most dominant language).
    languages = dominant_language_response["Languages"]
    LOGGER.debug("languages: %s", json.dumps(languages, indent=4))
    language = languages[0]
    LOGGER.debug("language: %s", json.dumps(language, indent=4))
    language_code = language["LanguageCode"]
    LOGGER.debug("language_code: %s", language_code)

    # Detect entities.
    detect_entities_response = COMPREHEND_CLIENT.detect_entities(
        Text=text,
        LanguageCode=language_code
    )
    LOGGER.debug("Response from detect_entities: %s", json.dumps(detect_entities_response, indent=4))
    entities = {}
    for entity in detect_entities_response["Entities"]:
        if entity["Type"] in entities:
            entities[entity["Type"]].append(entity["Text"])
        else:
            entities[entity["Type"]] = [ entity["Text"] ]
    LOGGER.debug("entities: %s", json.dumps(entities, indent=4))

    # Detect key phrases.
    detect_key_phrases_response = COMPREHEND_CLIENT.detect_key_phrases(
        Text=text,
        LanguageCode=language_code
    )
    LOGGER.debug("Response from detect_key_phrases: %s", json.dumps(detect_key_phrases_response, indent=4))
    key_phrases = []
    for key_phrase in detect_key_phrases_response["KeyPhrases"]:
        key_phrases.append(key_phrase["Text"])
    LOGGER.debug("key_phrases: %s", json.dumps(key_phrases, indent=4))

    # Detect PII entities.
    detect_pii_entities_response = COMPREHEND_CLIENT.detect_pii_entities(
        Text=text,
        LanguageCode=language_code
    )
    LOGGER.debug("Response from detect_pii_entities_response: %s", json.dumps(detect_pii_entities_response, indent=4))

    # Detect sentiment.
    detect_sentiment_response = COMPREHEND_CLIENT.detect_sentiment(
        Text=text,
        LanguageCode=language_code
    )
    LOGGER.debug("Response from detect_sentiment: %s", json.dumps(detect_sentiment_response, indent=4))
    sentiment = detect_sentiment_response["Sentiment"]
    LOGGER.debug("sentiment: %s", sentiment)

    # Detect syntax.
    detect_syntax_response = COMPREHEND_CLIENT.detect_syntax(
        Text=text,
        LanguageCode=language_code
    )
    LOGGER.debug("Response from detect_syntax: %s", json.dumps(detect_syntax_response, indent=4))
    syntax_tokens = {}
    for syntax_token in detect_syntax_response["SyntaxTokens"]:
        if syntax_token["PartOfSpeech"]["Tag"] in syntax_tokens:
            syntax_tokens[syntax_token["PartOfSpeech"]["Tag"]].append(syntax_token["Text"])
        else:
            syntax_tokens[syntax_token["PartOfSpeech"]["Tag"]] = [ syntax_token["Text"] ]
    LOGGER.debug("syntax_tokens: %s", json.dumps(syntax_tokens, indent=4))

    result = {
        "role": role,
        "text": text,
        "dominant_language": language_code,
        "entities": entities,
        "key_phrases": key_phrases,
        "sentiment": sentiment,
        "syntax_tokens": syntax_tokens
    }
    # Now also create a separate top-level array for each defined entity type.
    for entity_type in ENTITY_TYPES:
        if (entity_type in entities):
            result["entities_" + entity_type] = entities[entity_type]
        else:
            result["entities_" + entity_type] = []

    LOGGER.debug("Result: %s", json.dumps(result, indent=4))

    return result

# --------------------------------------------------------------------------------------------------

def write_insights(insights, destination_bucket_name, destination_object_key):
    LOGGER.debug("destination_object_key: %s", destination_object_key)
    response = S3_CLIENT.put_object(
        Body        = json.dumps(insights),
        Bucket      = destination_bucket_name,
        ContentType = "application/json",
        Key         = destination_object_key,
    )
    LOGGER.debug("Response: %s", response)

# --------------------------------------------------------------------------------------------------
