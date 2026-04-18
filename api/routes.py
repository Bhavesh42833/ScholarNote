from core.utils import response_model
from core.model import Job
from core.resources import get_sqs_client, get_dynamodb,get_vector_db
from retrieval.pipeline import retrival_pipeline
import json



def upload_handler(event):
    sqs=get_sqs_client()
    db=get_dynamodb()

    body=event.get("body","{}")

    if isinstance(body, str):
       body = json.loads(body)

    job=Job(**body)

    try:
        job.validate()
        if job.file_type.lower() == "query":
         sqs.send_message(message_body=body, action="query")
        else:
         sqs.send_message(message_body=body, action="ingest")
        db.create_file(job,ttl_seconds=86400,message="activating ingestion pipeline")
        return response_model(200, "Job validated and processing started")
    except Exception as e:
        raise e
    
async def query_handler(event):
    db=get_dynamodb()

    body=event.get("body","{}")
    if isinstance(body, str):
       body = json.loads(body)

    job=Job(**body)
    print("Job created from request body:", job)
    query=body.get("query","")

    try:
        job.validate()
        db.create_query(job, query=query, ttl_seconds=86400, message="Activating retrieval pipeline")
        result=await retrival_pipeline(job, query=query,model=None)
        return response_model(200, "", data=result)
    except Exception as e:
        raise e
    
def status_handler(event):
    db=get_dynamodb()

    body=event.get("body","{}")
    if isinstance(body, str):
       body = json.loads(body)

    job=Job(**body)

    try:
        job.validate()
        job_status=db.get_file_status(job)
        return response_model(200, "status retrieved successfully", data=job_status)
    except Exception as e:
        raise e
    
def delete_handler(event):

    sqs=get_sqs_client()
    db=get_dynamodb()

    body=event.get("body","{}")
    if isinstance(body, str):
       body = json.loads(body)

    job=Job(**body)

    try:
        job.validate()
        db.delete_file(job)
        sqs.send_message(message_body=body,action="delete")
        return response_model(200, "File deleted successfully")
    except Exception as e:
        raise e

async def delete_session_handler(event):
    vector_db=get_vector_db()

    body=event.get("body","{}")
    if isinstance(body, str):
       body = json.loads(body)

    session_id=body.get("session_id","")

    try:
        await vector_db.delete(session_id=session_id)
        return response_model(200, "Session data deleted successfully")
    except Exception as e:
        raise e
