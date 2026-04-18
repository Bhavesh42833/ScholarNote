import asyncio
import ast
import json
from groq import RateLimitError
from llama_index.core import Document
from core.logger import logger
from llama_index.core.node_parser import MarkdownNodeParser,SentenceSplitter
from core.database import pineconeDB
from retrieval.pipeline import retrival_pipeline

def video_transcript_to_chunked_Documents(transcript,metadata,job):

    logger.info(f"Transforming transcript to chunked Documents for job: {job.session_id}")
    
    documents=[]
    current_texts=""
    window_second=30
    window_start=0
    window_end=0
    
    """Iterating through transcript entries and creating chunked documents based on time windows of 30 seconds"""

    for entry in transcript:
        text = entry['text'].strip()
        start_time = round(entry['start'],2)
        duration = round(entry['duration'],2)
        end_time = start_time + duration
        if not text:
            continue

        if window_start == 0:
            window_start = start_time
            window_end = start_time + window_second

        if end_time-window_start < window_second:
            window_end = end_time
            current_texts += " " + text

        else:
            documents.append(Document(
                text=f"""name of video: {metadata.get('title', '')} 
                   type: {job.file_type}
                   context:{current_texts}""",
                metadata={
                    "source": job.video_url,
                    "file_id": job.file_id,
                    "file_name": metadata.get("title", ""),
                    "type": job.file_type,
                    "start_time": window_start,
                    "end_time": window_end,
                    "session_id": job.session_id
                }
            ))

            current_texts = ""
            window_start = start_time
            window_end = start_time + duration

    if not documents:
            logger.warning(f"No documents created from transcript for job: {job.session_id}")
        
    logger.info(f"Created {len(documents)} Documents from transcript for job: {job.session_id}")
    return documents

def pdf_to_chunked_Documents(documents,job):
     
     logger.info(f"Transforming PDF documents to chunked Documents for job: {job.session_id}")
     enriched_documents=[]

     """enriching documents with metadata and filtering out empty text documents"""

     for i,doc in enumerate(documents):
            text=doc.get_content()
            if not text:
                continue
            print(text[:200])
            enriched_documents.append(Document(
                text=text,
                metadata={
                    "file_id": job.file_id,
                    "file_name": job.file_name,
                    "type": job.file_type,
                    "page": doc.metadata.get("page_label", i+1),  # Use page_label if available, otherwise use index
                    "session_id": job.session_id
                }
            ))

     """chunking enriched documents using SentenceSplitter from llama_index"""

     splitter=SentenceSplitter(chunk_size=256, chunk_overlap=20,paragraph_separator="\n\n")

     chunked_documents=splitter.get_nodes_from_documents(enriched_documents)

     if not chunked_documents:
        logger.warning(f"No chunked documents created from PDF for job: {job.session_id}")

     """enriching chunked documents with metadata"""

     enriched_chunked_documents = []

     for i,doc in enumerate(chunked_documents):
        enriched_chunked_documents.append(Document(
          text= f""" name of document: {job.file_name}
                            type: {job.file_type}
                            context: {doc.text}""",
            metadata={
                **doc.metadata,
            }
        ))

     logger.info(f"Created {len(chunked_documents)} chunked Documents from PDF for job: {job.session_id}")
     return enriched_chunked_documents

def webpage_to_chunked_Documents(documents,job):
     logger.info(f"Transforming webpage documents to chunked Documents for job: {job.session_id}")
     enriched_documents=[]

     """enriching documents with metadata and filtering out empty text documents"""

    
     enriched_documents.append(Document(
                text=documents.text,
                metadata={
                    "file_id": job.file_id,
                    "web_url": job.web_url,
                    "type": job.file_type,
                    "session_id": job.session_id,
                    **documents.metadata
                }
            ))

     """chunking enriched documents using SentenceSplitter from llama_index"""

     splitter=MarkdownNodeParser()

     chunked_documents=splitter.get_nodes_from_documents(enriched_documents)

     final_chunked_documents=[]
     for doc in chunked_documents:
            text=doc.get_content()
            if len(text) > 512:
                sub_chunks =SentenceSplitter(chunk_size=256, chunk_overlap=20).get_nodes_from_documents([doc])
                final_chunked_documents.extend(sub_chunks)
            else:
                final_chunked_documents.append(doc)

     if not final_chunked_documents:
        logger.warning(f"No chunked documents created from webpage for job: {job.session_id}")

     """enriching chunked documents with metadata"""

     enriched_chunked_documents = []

     for i,doc in enumerate(final_chunked_documents):
        enriched_chunked_documents.append(Document(
          text= f"""  name of webpage: {doc.metadata.get("title", "")}
                            type: {job.file_type}
                            context: {doc.text}""",
            metadata={
                **doc.metadata,
            }
        ))

     logger.info(f"Created {len(final_chunked_documents)} chunked Documents from webpage for job: {job.session_id}")
     return enriched_chunked_documents

def transform_documents(documents,job):
    if job.is_pdf():
        docs=documents.get("documents", [])
        return pdf_to_chunked_Documents(documents=docs,job=job)
    elif job.is_webpage():
        docs=documents.get("documents", [])
        return webpage_to_chunked_Documents(documents=docs,job=job)
    else:
        transcript=documents.get("transcript", [])
        metadata=documents.get("metadata", {})
        return video_transcript_to_chunked_Documents(transcript,metadata,job)



async def embedding_chunked_Documents(chunked_documents, embedding_model, job):
    logger.info(f"Embedding chunked Documents for job: {job.session_id}")

    texts = [doc.text for doc in chunked_documents]
    vectors = await embedding_model.embed_query(queries=texts, isquery="false")

    embedded_vector = [
        {
            "id": f"{job.file_id}_chunk{i}",
            "values": vector,
            "metadata": {
                "text": doc.text,
                **doc.metadata
            }
        }
        for i, (doc, vector) in enumerate(zip(chunked_documents, vectors))
    ]

    logger.info(f"Completed embedding {len(embedded_vector)} chunks for job: {job.session_id}")
    return embedded_vector

async def store_embeddings(embedding_vector,db,job):
    await db.upsert_vectors(embedding_vector,job)

async def classify_query_using_llm(query,chat_model):
    logger.info("Classifying query using LLM")
    try:
        system_prompt="""You are an expert Data Extraction Engine. Your goal is to parse exam documents provided in Markdown and convert them into a valid JSON array.

### EXTRACTION RULES:
1. QUESTION_TEXT INTEGRITY: You MUST preserve the exact Markdown syntax within the "question_text" field. 
   - Tables must keep their pipe (|) and dash (---) structure.
   - Do NOT skip any rows or columns in tables.
   - Preserve all bolding (**), italics (*), and list items.
   - LaTeX/Math formulas must remain exactly as they appear.

2. QUOTE ESCAPING: Since you are outputting JSON, you must properly escape any double quotes (") found within the Markdown text using a backslash (\").

3. LOGIC:
   - question_number: Capture the exact label (e.g., "1(a)", "Section A, Q1").
   - marks: Extract as an integer. If no marks are found, set to null.
   - summary:
        1. Create a search-optimized summary of the question.
        2. If the question contains a table, describe the columns and the core data (e.g., "Comparison of tax rates between 2023 and 2024").
        3. Include keywords that a student or teacher might use to find this specific problem (e.g., "Compound Interest", "Photosynthesis Diagram").
        4. Keep it under 30 words. This will be used as the primary text for searching in vector database.

### OUTPUT FORMAT:
Return ONLY a valid JSON array of objects. Do not include any introductory text, markdown code blocks (like ```json), or follow-up commentary.

### SCHEMA:
[
  {
    "question_number": "string",
    "question_text": "string (Full raw markdown with escaped quotes)",
    "marks": integer or null,
    "summary": "string (A concise summary of the question, max 20 words)",
  }
]"""

        user_prompt=f"""
        Input: {query}"""
        
        message=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ]

        response= await chat_model.chat(message,model="llama-3.3-70b-versatile",temperature=0)
        print(f"LLM classification response: {response}")
        questions=json.loads(response)
        classified_questions={}
        classified_questions["Part1"]=[]
        classified_questions["Part2"]=[]
        for i,q in enumerate(questions):
            if(i< len(questions)//2):
                classified_questions["Part1"].append(q)
            else:
                classified_questions["Part2"].append(q)
        return classified_questions
    except Exception as e:
        logger.error(f"Error classifying query using LLM: {str(e)}")
        raise e

async def process_easy_group(questions,job,model="qwen/qwen3-32b"):
    results = []
    for q in questions:
        while True:
            try:
                result = await retrival_pipeline(job,f"question:{q.get('summary')},marks:{q.get('marks')}",model)
                results.append(result)
                # small breathing room between requests
                await asyncio.sleep(1)
                break
            except RateLimitError as e:
                wait = e.response.headers.get("retry-after", 5)  # default to 5 seconds if header is missing
                await asyncio.sleep(wait + 1)
            except Exception as e:
                logger.error(f"Error processing easy group question group for job: {job.session_id} - {str(e)}")
                raise e
    return results

async def process_hard_group(questions,job,model="openai/gpt-oss-120b"):
    results = []
    for q in questions:
        while True:
            try:
                result = await retrival_pipeline(job,f"question:{q.get('summary')},marks:{q.get('marks')}",model)
                results.append(result)
                # small breathing room between requests
                await asyncio.sleep(1)
                break
            except RateLimitError as e:
                wait = e.response.headers.get("retry-after", 5)  # default to 5 seconds if header is missing
                await asyncio.sleep(wait + 1)
            except Exception as e:
                logger.error(f"Error processing hard group question group for job: {job.session_id} - {str(e)}")
                raise e
    return results

async def run_queries(queries,job,llm):
    logger.info(f"Running queries for job: {job.session_id} with queries: {queries}")
    easy_group=queries.get("Part1", [])
    hard_group=queries.get("Part2", [])

    easy_results,hard_results=await asyncio.gather(
        process_easy_group(easy_group,job,model="qwen/qwen3-32b"),
        process_hard_group(hard_group,job,model="openai/gpt-oss-120b")
    )
    
    result=[]
    for i,q in enumerate(easy_group):
        result.append({
            "serialNumber": q.get("question_number"),
            "question": q.get("question_text"),
            "answer": easy_results[i].get("answer", "No answer generated"),
            "references": easy_results[i].get("references", [])
        })
    for i,q in enumerate(hard_group):
        result.append({
            "serialNumber": q.get("question_number"),
            "question": q.get("question_text"),
            "answer": hard_results[i].get("answer", "No answer generated"),
            "references": hard_results[i].get("references", [])
        })
    
    logger.info(f"Completed running queries for job: {job.session_id} with result: {result}")
    return result


    