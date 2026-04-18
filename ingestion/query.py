import json
from core.logger import logger
from ingestion.loader import parse_query, upload_results
from ingestion.tranformers import run_queries,classify_query_using_llm
import asyncio
from core.resources import get_chat_model, get_dynamodb


async def query_pipeline(job,db):
   loop=asyncio.get_event_loop()
   chat_model= get_chat_model()
   loop.run_in_executor(None, db.update_status, job, "in_progress", "Starting query processing")
   logger.info(f"Starting query pipeline for job: {job.session_id}")
   try:
      
      loop.run_in_executor(None, db.update_status, job, "in_progress", "Parsing query from input")
      query=await parse_query(job)

      loop.run_in_executor(None, db.update_status, job, "in_progress", "Classifying queries")
      classified_queries=await classify_query_using_llm(query,chat_model)
    
      loop.run_in_executor(None, db.update_status, job, "in_progress", "Running queries against the document")
      results=await run_queries(classified_queries,job,chat_model)

      loop.run_in_executor(None, db.update_status, job, "completed", "Query processing completed")
      await upload_results(job,results)
      logger.info(f"Completed query pipeline for job: {job.session_id} with results: {results}")
   except Exception as e:
        logger.error(f"Error in query pipeline for job: {job.session_id} - {str(e)}")
        loop.run_in_executor(None, db.update_status, job, "failed", f"Query processing failed: {str(e)}")
 

