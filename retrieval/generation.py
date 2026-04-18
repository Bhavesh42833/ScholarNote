from core.logger import logger
import re


async def query_generation(query,chat_model,job,model="llama-3.1-8b-instant"):
    logger.info(f"Generating query for job: {job.session_id} with input query: {query}")
    prompt=f""" The goal is to create 2 concise and effective queries or input prompts that refines the user's question while maximizing the relevance of retrieved documents but still keeping the original intent.
            Rules:
        - Output ONLY the queries, one per line
        - No numbering, no bullets, no prefixes
        - No explanations or extra text
        - Each query on its own line
    input query: {query} """
    message=[
        {"role":"system","content":"You are a helpful assistant that generates an optimized query for retrieving relevant information from a document database."},
        {"role":"user","content":prompt}
    ]
    try:
        generated_query=await chat_model.chat(message,model=model)
        logger.info(f"Generated query for job: {job.session_id} : {generated_query}")

        queries=[line.strip() for line in generated_query.strip().split('\n') if line.strip()]
        queries.append(query)  
        print(queries)
        return queries
    except Exception as e:
        logger.error(f"Error generating query for job: {job.session_id} : {str(e)}")
        raise e

async def response_generation(query,context,chat_model,job,ref_map,model=None):
    logger.info(f"Generating response for job: {job.session_id} with query: {query} and context: {context} using model: {model}")
    system_prompt=f"""You are a helpful assistant that answers questions using the provided context.
                   Rules:
                    - Always cite sources inline using [1], [2] etc. immediately after the information.The numbers should correspond to the provided reference list at the end.
                    - Use square brackets only not any other brackets for inline citations.
                    - Font size should be constant for all answers and should not be used to differentiate between different parts of the answer. Use font weight (bold) instead.
                    - If the answer is partially or fully outside the context, answer correctly but clearly state which parts are not from the context
                    - Be concise and direct — avoid unnecessary preamble and do not include <think> tag.
                    - Max limit of Words is 300 and if marks present then answer according to marks distribution."""

    user_prompt = """Context:
                    {context}

                    Question: {query}

                    Answer (with inline citations):"""
    message=[
        {"role":"system","content":system_prompt},
        {"role":"user","content":user_prompt.format(context=context, query=query)}
    ]
    try:
        response=await chat_model.chat(message,model=model)
        
        res={
            "answer": response,
            "references": ref_map
        }
        logger.info(f"Generated response for job: {job.session_id} : {response}")
        return res
    except Exception as e:
        logger.error(f"Error generating response for job: {job.session_id} : {str(e)}")
        raise e
    

