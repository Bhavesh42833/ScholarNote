import boto3
import os
from core.logger import logger
from core.exceptions import jobProcessingError
from llama_index.core import Document
from llama_cloud import AsyncLlamaCloud
from firecrawl import Firecrawl
from core.utils import youtube
import json

s3 = boto3.client("s3")

def download_from_s3(job):
    logger.info(f"Downloading file from S3 for job: {job.session_id}")
    ext= "pdf" if job.file_type.lower() == "query" else "json"
    local_path = f"/tmp/{job.file_id}.{ext}"
    try:
      res=s3.download_file(job.s3_bucket, job.s3_key, local_path)
      if res is not None:
        raise jobProcessingError("Failed to download file from S3: " + str(res))
      else:
        logger.info(f"File downloaded to: {local_path}")

        return local_path
    except jobProcessingError as e:
      logger.error("Error downloading file from S3: " + str(e))
      raise e


def load_pdf(job):
    logger.info(f"Loading PDF for job: {job.session_id}")
    local_path = download_from_s3(job)

    if local_path is None:
        raise jobProcessingError("Local path does not exist after download")

    try:
        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        documents = [Document(text=entry["text"], metadata=entry.get("metadata", {})) for entry in data]

        if not documents:
          raise jobProcessingError("No documents found in the specified directory")
       
        logger.info(f"Loaded {len(documents)} documents for job: {job.session_id} : " )
       
        for i in range(min(3, len(documents))):
          logger.info(f"Document {i+1} content preview: {documents[i]}...")
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error loading PDF for job {job.session_id}: {str(e)}")
        raise jobProcessingError("Failed to load PDF: " + str(e))
    
async def load_webpage(job):
    logger.info(f"Loading webpage for job: {job.session_id}")
    try:
        app=Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY"))
        scrape_result= app.scrape(url=job.web_url,
            exclude_tags=["a", "img", "figure", "nav", "footer", "script", "style"],
            only_main_content= True,
            formats= ["markdown"]
        ) 
        
        documents=Document(text=scrape_result.markdown)
        documents.metadata["title"]=scrape_result.metadata.title
        print(documents.metadata)
        if not documents:
          raise jobProcessingError("No documents found in the webpage")
        logger.info(f"Loaded documents from webpage for job: {job.session_id}")
        logger.info(f"Document content preview: {documents.text[:200]}...") 
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error loading webpage for job {job.session_id}: {str(e)}")
        raise jobProcessingError("Failed to load webpage: " + str(e))

def load_video(job):
    logger.info(f"Loading video for job: {job.session_id}")
    yt=youtube()
    content=yt.get_video_transcript(url=job.video_url)

    transcript=content["formatted"]
    logger.info(f"Transcript preview for job {job.session_id}: {transcript[:200]}...")
    metadata=yt.get_video_metadata(url=job.video_url)
    return {"transcript": transcript, "metadata": metadata}

async def loader(job):
    if job.is_pdf():
        return load_pdf(job)
    elif job.is_webpage():
        return await load_webpage(job)
    else:
        return load_video(job)
    
async def parse_query(job):
    logger.info(f"Parsing query for job: {job.session_id}")
    LlamaParse= AsyncLlamaCloud(api_key=os.environ.get("LLAMA_CLOUD_API_KEY"))
    query=""
    local_path = download_from_s3(job)

    if local_path is None:
        raise jobProcessingError("Local path does not exist after download")
    try:
        file_obj=await LlamaParse.files.create(file=local_path, purpose="parse")
        response=await LlamaParse.parsing.parse(
            file_id=file_obj.id,
            tier="cost_effective",
            version="latest",
            output_options={"markdown":{ "tables" :{"output_tables_as_markdown": True}}},
            expand=["markdown"]
        )
        print(response)
        query=response.markdown.pages[0].markdown
        logger.info(f"Parsed query for job: {job.session_id} - {query[:100]}...")  # Log first 100 chars of query
        return query
    except Exception as e:
        logger.error(f"Error parsing query for job: {job.session_id} - {str(e)}")
        raise e
    
async def upload_results(job,results):
    logger.info(f"Uploading results to S3 for job: {job.session_id}")
    folder_name=job.s3_key.split("/")[0]
    s3_key=f"{folder_name}/results.json"
    try:
        s3.put_object(Bucket=job.s3_bucket, Key=s3_key, Body=json.dumps(results))
        logger.info(f"Results uploaded to S3 at key: {s3_key} for job: {job.session_id}")
    except Exception as e:
        logger.error(f"Error uploading results to S3 for job: {job.session_id} - {str(e)}")
        raise e






   