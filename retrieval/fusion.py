from core.logger import logger


def deduplicate_docs(docs):
    logger.info("Deduplicating retrieved documents")
    seen = set()
    unique_docs = []

    for doc in docs:
        key = doc.get("id")

        if key not in seen:
            seen.add(key)
            unique_docs.append(doc)
    print(f"Unique documents after deduplication: {unique_docs}")

    return unique_docs

async def rerank_batch(docs, query, llm):
    logger.info("Reranking retrieved documents")
    passages = [doc.get("metadata", {}).get("text") for doc in docs]

    reranked = await llm.rerank(query=query, documents=passages, top_k=len(docs))

    return [docs[r.index] for r in reranked]

def diverse_rerank(reranked_docs, top_k=3):
    file_groups = {}
    for doc in reranked_docs:
        file_id = doc.get("metadata", {}).get("file_id")
        if file_id not in file_groups:
            file_groups[file_id] = []
        file_groups[file_id].append(doc)

    result = []

    for file_id, docs in file_groups.items():
        if docs:
            result.append(docs[0])  
            file_groups[file_id] = docs[1:]  

    remaining = []
    for docs in file_groups.values():
        remaining.extend(docs)

    remaining = sorted(remaining, key=lambda x: x.get("score", 0), reverse=True)
    result.extend(remaining[:top_k - len(result)])

    return result[:top_k]

def build_context(docs):
    logger.info("Building context from retrieved documents")
    context_parts = []
    ref_map={}
    
    for i, doc in enumerate(docs, 1):
        content = doc.get("metadata", {}).get("text", "").strip()
        
        ref_map[i]={
            "file_id": doc.get("metadata",{}).get("file_id", "unknown"),
            "file_name": doc.get("metadata",{}).get("file_name", "unknown"),
            "type": doc.get("metadata",{}).get("type", "unknown"),
            "text_snippet": doc.get("metadata",{}).get("text", ""),  # Include a snippet of the text
            "page": doc.get("metadata",{}).get("page", "unknown"),  # Include page number if available
            "video_url": doc.get("metadata",{}).get("source", "unknown"), # Include video URL if available
            "start_time": doc.get("metadata",{}).get("start_time", "unknown"),  # Include start time if available
            "end_time": doc.get("metadata",{}).get("end_time", "unknown"),
            "header": doc.get("metadata",{}).get("header_path", "unknown")   # Include header if available
        }
        context_parts.append(f"[{i}] : {content}")
        logger.info(f"Context part for doc {i}: {content[:100]}...")  # preview first 100 chars

    full_context = "\n\n".join(context_parts)
    logger.info(f"Total context length: {len(full_context)} characters")
    return full_context, ref_map