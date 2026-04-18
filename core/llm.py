from core.logger import logger
import os
import asyncio


class llm:
    def __init__(self, chat_model=["openai/gpt-oss-120b","llama-3.3-70b-versatile","llama-3.1-8b-instant"], embedding_model="Voyage-3.5-lite"):
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self._embedding_model_instance = None
        self._chat_model_instance = None
        self._embedding_loop_id = None
        self._chat_loop_id = None

    def initialize_embedding(self):
        # Just store config, don't create the client yet
        logger.info(f"Embedding model configured: {self.embedding_model}")

    def initialize_chat_model(self):
        # Just store config, don't create the client yet
        logger.info(f"Chat model configured: {self.chat_model}")

    def _get_embedding_instance(self):
        """Lazy init — always created inside the running loop."""
        import voyageai

        loop = asyncio.get_running_loop()
        if self._embedding_model_instance is None or self._embedding_loop_id != id(loop):
            logger.info(f"Creating voyageai client on loop: {id(loop)}")
            self._embedding_model_instance =  voyageai.AsyncClient(
            api_key=os.environ.get("VOYAGE_API_KEY")
        )
            self._embedding_loop_id = id(loop)
        return self._embedding_model_instance

    def _get_chat_instance(self):
        """Lazy init — always created inside the running loop."""
        from groq import AsyncGroq
        loop = asyncio.get_running_loop()
        if self._chat_model_instance is None or self._chat_loop_id != id(loop):
            logger.info(f"Creating AsyncGroq client on loop: {id(loop)}")
            self._chat_model_instance = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
            self._chat_loop_id = id(loop)
        return self._chat_model_instance

    async def embed_query(self, queries, isquery="true"):
        instance = self._get_embedding_instance() 
        input_type = "query" if isquery == "true" else "document"
        result = await instance.embed(
                queries, 
                model="voyage-3.5-lite",
                input_type=input_type,
                output_dimension=512
            )
        return result.embeddings 

    async def rerank(self, query: str, documents: list[str], top_k: int = 15):
        instance = self._get_embedding_instance()  
        result = await instance.rerank(
            query=query,
            documents=documents,
            model="rerank-2.5-lite",
            top_k=top_k
        )
        return result.results 
        

    async def chat(self, message, model=None,temperature=0.5):
        logger.info(f"Generating response for message: {message}")
        instance = self._get_chat_instance() 
        if model is not None:
            try:
                    logger.info(f"Trying chat model: {model}")            
                    response = await instance.chat.completions.create(
                        model=model,
                        messages=message,
                        temperature=temperature,
                        top_p=0.9
                    )
                    return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error occurred with chat model {model}: {e}")
                raise e
        else:
            for m in self.chat_model:
                try:
                        logger.info(f"Trying chat model: {m}")            
                        response = await instance.chat.completions.create(
                            model=m,
                            messages=message,
                            temperature=temperature,
                            top_p=0.9
                        )
                        return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Error occurred with chat model {m}: {e}")
                    continue
            raise e