import boto3
import json
import os
from core.logger import logger

class sqsClient:
    def __init__(self):
        logger.info("Initializing SQS client")
        self.sqs = boto3.client("sqs",region_name=os.environ.get("AWS_REGION","us-east-1"))
        self.queue_url = os.environ.get("SQS_QUEUE_URL")

    def send_message(self, message_body: dict,action):
        message={
            "action": action,
            "job": message_body
        }
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message)
            )
            logger.info(f"Message sent to SQS with ID: {response.get('MessageId')}")
        except Exception as e:
            logger.error(f"Error sending message to SQS: {str(e)}")
            raise e