import os


_chat_model = None
_embedding_model = None
_vector_db = None
_sqs_client = None
_dynamodb_resource = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from core.llm import llm
        _embedding_model = llm()
        # No heavy init here — HuggingFace client created lazily inside embed_query()
    return _embedding_model

def get_chat_model():
    global _chat_model
    if _chat_model is None:
        from core.llm import llm
        _chat_model = llm()
        # No heavy init here — AsyncGroq client created lazily inside chat()
    return _chat_model

def get_vector_db():
    global _vector_db
    if _vector_db is None:
        from core.database import pineconeDB
        _vector_db = pineconeDB()
        # Pinecone Index created lazily inside upsert_vectors()
    return _vector_db

def get_sqs_client():
    global _sqs_client
    if _sqs_client is None:
        from core.aws import sqsClient
        _sqs_client = sqsClient()  # boto3 — sync, no loop issues
    return _sqs_client

def get_dynamodb():
    global _dynamodb_resource
    if _dynamodb_resource is None:
        from core.database import DynamoDB
        _dynamodb_resource = DynamoDB()  # boto3 — sync, no loop issues
    return _dynamodb_resource


