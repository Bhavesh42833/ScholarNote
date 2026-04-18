import os
import json
from core.logger import logger
import asyncio
from core.model import Job
from core.resources import get_dynamodb, get_vector_db
import nest_asyncio

nest_asyncio.apply()

async def main_handler(event,context):
    logger.info(f"Received event: {event}")

    db_status=get_dynamodb()
    vector_db=get_vector_db()
    
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])

            job = Job(**body["job"])
            action = body["action"]

            if action == "ingest":
                from ingestion.pipeline import ingestion_pipeline
                await ingestion_pipeline(job, db_status)

            elif action == "delete":
              await  vector_db.delete_vectors(job)
              logger.info(f"Deleted vectors for job: {job.session_id},file: {job.file_id} from vector database")

            elif action == "query":
                from ingestion.query import query_pipeline
                await query_pipeline(job,db_status)

        except Exception as e:
            logger.error(f"Job failed: {e}", exc_info=True)
            raise e

def handler(event, context):
    asyncio.run(main_handler(event, context))
