import os

import boto3
from boto3.dynamodb.conditions import Key, Attr

from common.utils.lambda_utils import load_path_parameter_from_event
from common.utils.error_handler import (
    error_response,
    internal_server_error,
    not_found_error,
)
from common.utils.response_utils import success_response

table_name = os.getenv("MEMORY_TABLE_NAME")
memory_table = boto3.resource("dynamodb").Table(table_name)


def parse_and_validate(event):
    session_id = load_path_parameter_from_event(event, "session_id")
    if not session_id:
        raise ValueError("session_id is required")
    session_id = f"SESSION#{session_id}"
    return session_id


def clean_messages_and_metadata_items(message_items, metadata_items):
    # Extract metadata while filtering out the 'pk' key
    metadata = (
        {key: val for key, val in metadata_items[0].items() if key != "pk"}
        if metadata_items
        else {}
    )

    # Extract messages focusing only on the content inside the 'message' dictionary
    messages = [msg["message"] for msg in message_items if "message" in msg]

    return messages, metadata


def lambda_handler(event, context):
    try:
        session_id = parse_and_validate(event)

        res_session = memory_table.query(
            KeyConditionExpression=Key("pk").eq(session_id), 
            FilterExpression=Attr("is_deleted").eq(False)
        )
        session_items = res_session.get("Items", [])

        if not session_items:
            return not_found_error()
        
        session = session_items[0]
        return success_response(session)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return internal_server_error()
