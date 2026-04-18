from core.logger import logger
import asyncio


async def multiquery_retriever(job, retriever, queries, llm):
    logger.info(f"Invoking multiquery_retriever for job: {job.session_id}")
    cleaned_queries = [q.strip().strip('"') for q in queries]
    
    file=job.selected_file_ids

    embeddings = await asyncio.gather(*[
        llm.embed_query(queries, isquery="true") for queries in cleaned_queries
    ])

    tasks = []
    for emb in embeddings:
        for file_id in file:
            tasks.append(retriever.query_vectors(vector=emb, job=job,file_id=file_id))
        
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_docs = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"One of the multi-queries failed: {result}")
            continue
        all_docs.extend(result.matches)

    return all_docs