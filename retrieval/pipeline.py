import time
from core.logger import logger
from retrieval.fusion import build_context, deduplicate_docs, diverse_rerank
from retrieval.generation import query_generation, response_generation
from retrieval.retrievers import multiquery_retriever
from retrieval.fusion import rerank_batch
from core.resources import get_chat_model, get_dynamodb, get_embedding_model, get_vector_db
import asyncio



async def retrival_pipeline(job,query,model):
    loop=asyncio.get_event_loop()

    chat_model= get_chat_model()
    embedding_model= get_embedding_model()
    vector_db= get_vector_db()
    db=get_dynamodb()

    stages={}
    logger.info(f"Starting retrieval pipeline for job: {job.session_id} with query: {query}")

    try:
        t=time.time()
        loop.run_in_executor(None, db.update_status, job, "in_progress", "Generating additional queries for accurate retrieval")
        queries=await query_generation(query,chat_model=chat_model,job=job)
        stages["3 query_generation"]=f"{time.time()-t:.2f}s"

        t=time.time()
        loop.run_in_executor(None, db.update_status, job, "in_progress", "Retrieving relevant documents using multiple queries")
        docs=await multiquery_retriever(job,retriever=vector_db,queries=queries,llm=embedding_model)
        stages["multiquery_retriever"]=f"{time.time()-t:.2f}s"

        t=time.time()
        loop.run_in_executor(None, db.update_status, job, "in_progress", "Deduplicating retrieved documents")
        unique_docs=deduplicate_docs(docs)
        stages["deduplicate_docs"]=f"{time.time()-t:.2f}s"

        t=time.time()
        loop.run_in_executor(None, db.update_status, job, "in_progress", "Reranking retrieved documents")
        reranked_docs=await rerank_batch(docs=unique_docs,query=query,llm=chat_model)
        stages["rerank_batch"]=f"{time.time()-t:.2f}s"

        t=time.time()
        loop.run_in_executor(None, db.update_status, job, "in_progress", "Incorporating diversity in reranking to ensure varied sources")
        top_k_docs=diverse_rerank(reranked_docs, top_k=5)
        stages["diverse_rerank"]=f"{time.time()-t:.2f}s"

        t=time.time()
        loop.run_in_executor(None, db.update_status, job, "in_progress", "Building context from retrieved documents for response generation")
        context,ref_map=build_context(top_k_docs)
        stages["build_context"]=f"{time.time()-t:.2f}s"

        t=time.time()
        loop.run_in_executor(None, db.update_status, job, "in_progress", "Generating response based on retrieved context")
        res=await response_generation(query=query,job=job,context=context,ref_map=ref_map,chat_model=chat_model,model=model)
        stages["response_generation"]=f"{time.time()-t:.2f}s"

        logger.info(f"Completed retrieval pipeline for job: {job.session_id} with response: {res}")
        logger.info(f"Stage-wise timing for job: {job.session_id} : {stages}")
        loop.run_in_executor(None, db.update_status, job, "completed", "Retrieval pipeline completed successfully")
        return res
    except Exception as e:
        logger.error(f"Error in retrieval pipeline for job: {job.session_id} - {str(e)}")
        loop.run_in_executor(None, db.update_status, job, "failed", "Failed to complete retrieval pipeline : " + str(e))
        raise e
