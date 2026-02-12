# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os

import boto3

QUEUE_URL = os.environ["NR_QUEUE"]

sqs = boto3.client("sqs")


def lambda_handler(event, _) -> dict:
    # Check for any message on queue
    response = sqs.receive_message(QueueUrl=QUEUE_URL)
    print(f"SQS response was: {json.dumps(response)}")
    if len(response.get("Messages", [])) == 0:
        print("No messages in queue, continuing deployment")
        return {"Directive": "CONTINUE"}

    # Any message is taken as indication of issue
    # Attempt to parse the "reason" field out of it to return to AWS AppConfig
    print("Failure message found on queue, rolling back")
    message = response["Messages"][0]
    try:
        details = json.loads(message["Body"])
        reason = details["reason"]
    except Exception:
        print("Failed to parse message body as JSON")
        reason = "(Could not parse message body for a reason)"

    # Delete any received messages
    try:
        for message in response["Messages"]:
            sqs.delete_message(
                QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"]
            )
    except Exception:
        # Messages expire in a minute anyway and we don't want to prevent
        # returning our response to AppConfig
        pass

    return {"Directive": "ROLL_BACK", "Description": reason}


if __name__ == "__main__":
    lambda_handler(None, None)
