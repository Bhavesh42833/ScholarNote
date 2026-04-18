from core.logger import logger
from ingestion.loader import loader
from ingestion.tranformers import transform_documents, embedding_chunked_Documents,store_embeddings
from core.resources import get_embedding_model, get_vector_db
import asyncio
       

async def ingestion_pipeline(job,db_status):
    
    loop = asyncio.get_running_loop()

    embedding_model= get_embedding_model()
    db_vector=get_vector_db()

   
    logger.info(f"Starting ingestion pipeline for job: {job.session_id}")
    try:
        message = lambda job: "Parsing PDF" if job.file_type == "pdf" else "Fetching video transcript" if job.file_type == "video" else "Scraping webpage"
        await loop.run_in_executor(None, db_status.update_status, job, "in_progress",message(job))
        # Step 1: Load the file and convert to Documents
        documents = await loader(job)
        
        # Step 2: Transform the Documents (e.g., chunking, enriching metadata)
        
        await loop.run_in_executor(None, db_status.update_status, job, "in_progress", "chunking and enriching metadata")
        transformed_documents = transform_documents(documents, job)

        # Step 3: Generate embeddings and store in vector database
        await loop.run_in_executor(None, db_status.update_status, job, "in_progress", "generating embeddings")
        embedding_vector = await embedding_chunked_Documents(chunked_documents=transformed_documents,embedding_model=embedding_model,job=job )

        await loop.run_in_executor(None, db_status.update_status, job, "in_progress", "storing embeddings")
        await store_embeddings(embedding_vector,db=db_vector, job=job)

        # Step 4: Update status in DynamoDB
        await loop.run_in_executor(None, db_status.update_status, job, "completed", "successfull")
        logger.info(f"Completed ingestion pipeline for job: {job.session_id}")

    except Exception as e:
        logger.error(f"Error in ingestion pipeline for job: {job.session_id} - {str(e)}")
        await loop.run_in_executor(None, db_status.update_status, job, "error", f"Ingestion pipeline failed: {str(e)}")
        raise e