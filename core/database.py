from pinecone import Pinecone,PineconeAsyncio,ServerlessSpec
import os
from core.logger import logger
import boto3
import time
from core.utils import db_operation
import asyncio


class pineconeDB:
    def __init__(self):
        api_key = os.environ.get("PINECONE_API_KEY")
        index_name = os.environ.get("PINECONE_INDEX")
        self._api_key = api_key
        self._index_cache: dict[int, any] = {}  # loop_id -> index

        sync_client = Pinecone(api_key=api_key)
        if not sync_client.has_index(index_name):
            sync_client.create_index(
                name=index_name,
                dimension=512,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        self.index_host = sync_client.describe_index(index_name).host

    def _get_index(self):
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
        if loop_id not in self._index_cache:
            client = PineconeAsyncio(api_key=self._api_key)
            self._index_cache[loop_id] = client.IndexAsyncio(host=self.index_host)
        return self._index_cache[loop_id]

    async def upsert_vectors(self, vectors: list,job):
        await self._get_index().upsert(vectors=vectors,namespace=job.session_id)

    async def query_vectors(self, vector, job,file_id):
        return await self._get_index().query(
            namespace=job.session_id,
            vector=vector,
            top_k=3,
            include_metadata=True,
            filter={"file_id": file_id}  
        )
    
    @db_operation(lambda self,job: f"Deleting vectors from Pinecone database for job: {job.session_id}, file: {job.file_id}")
    async def delete_vectors(self,job) -> None:
      file_id = job.file_id
      session_id = job.session_id
      await self._get_index().delete(filter={"file_id": file_id},namespace=session_id)

    async def delete(self,session_id):
        await self._get_index().delete(delete_all=True,namespace=session_id)

class DynamoDB:
    @db_operation(lambda self: f"Initializing DynamoDB client")
    def __init__(self):
        table_name = os.environ.get("DYNAMODB_TABLE_NAME", "Docchat_Events_Tracker")
        self.dynamodb = boto3.resource("dynamodb",region_name=os.environ.get("AWS_REGION","us-east-1"))
        self.table = self.dynamodb.Table(table_name)
    

    @db_operation(lambda self,job,**kwargs: f"Creating file entry in DynamoDB for job: {job.session_id}, file: {job.file_id}")
    def create_file(self, job, ttl_seconds: int = None,message:str=""):
        file_prefix= "QUERY#" if job.file_type=="query" else "FILE#"
        item = {
            "session_id": job.session_id,
            "file_id": f"{file_prefix}{job.file_id}",
            "file_name": job.file_name or "",
            "type": job.file_type,
            "pipeline": "ingestion",
            "status": "processing",
            "message": message,
            "created_at": int(time.time()),
        }

        if ttl_seconds:
            item["ttl"] = int(time.time()) + ttl_seconds
        self.table.put_item(Item=item)

    @db_operation(lambda self,job,query,**kwargs: f"Creating query entry in DynamoDB for job: {job.session_id}, file: {job.file_id}, query: {query}")
    def create_query(self, job, query: str, ttl_seconds: int = None,message:str=""):
        file_prefix= "QUERY#" if job.file_type=="query" else "FILE#"
        item = {
            "session_id": job.session_id,
            "file_id": f"{file_prefix}{job.file_id}",
            "query": query,
            "pipeline": "retrieval",
            "message": message,
            "status": "processing",
            "selected_docs": job.selected_file_ids or [],
            "created_at": int(time.time()),
        }

        if ttl_seconds:
            item["ttl"] = int(time.time()) + ttl_seconds
        self.table.put_item(Item=item)


    @db_operation(lambda *args: f"Updating file status in DynamoDB for job: {args[1].session_id}, file: {args[1].file_id} : {args[2]}")
    def update_status(self, job, status: str,message:str=""):
            file_prefix= "QUERY#" if job.file_type=="query" else "FILE#"
            self.table.update_item(
                Key={
                    "session_id": job.session_id,
                    "file_id": f"{file_prefix}{job.file_id}"
                },
                UpdateExpression="SET #s = :val,#m=:msg",
                ExpressionAttributeNames={"#s": "status", "#m": "message"},
                ExpressionAttributeValues={":val": status, ":msg": message}
            )

    @db_operation(lambda self,job: f"Fetching all files for session: {job.session_id}")
    def get_files(self, job):
        response = self.table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": job.session_id}
        )
        return response.get("Items", [])

    @db_operation(lambda self,job: f"Fetching deleted file IDs for session: {job.session_id}")
    def get_deleted_files(self, job):
        items = self.get_files(job)

        return [
            item["file_id"]
            for item in items
            if item.get("status") == "deleted"
        ]

    @db_operation(lambda self,job: f"Soft deleting file in DynamoDB for job: {job.session_id}, file: {job.file_id}")
    def delete_file(self, job):
        self.update_status(job, "deleted")

    @db_operation(lambda self,job: f"Hard deleting file from DynamoDB for job: {job.session_id}, file: {job.file_id}")
    def hard_delete_file(self, job):
        self.table.delete_item(
            Key={
                "session_id": job.session_id,
                "file_id": job.file_id
            }
        )
    @db_operation(lambda self,job: f"Getting file status from DynamoDB for job: {job.session_id}, file: {job.file_id}")
    def get_file_status(self, job):
        file_prefix= "QUERY#" if job.file_type=="query" else "FILE#"
        response = self.table.get_item(
            Key={
                "session_id": job.session_id,
                "file_id": f"{file_prefix}{job.file_id}"
            }
        )
        item = response.get("Item")
        return [item.get("status"),item.get("message")] if item else None