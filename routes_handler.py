import asyncio

from core.exceptionHandler import handle_exception
from core.utils import response_model
from api.routes import upload_handler, query_handler, status_handler, delete_handler,delete_session_handler
from core.logger import logger


SYNC_ROUTES ={
    ("POST","/upload"): upload_handler,
    ("POST","/delete"): delete_handler,
    ("POST","/status"): status_handler,
}

ASYNC_ROUTES={
    ("POST","/query"): query_handler,
    ("POST","/reset"): delete_session_handler
}


def handler(event,context):
    
    logger.info(f"Received event: {event}")
    try:
        path = event.get("rawPath", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        route_handler = SYNC_ROUTES.get((method, path))

        if route_handler:
            return  route_handler(event)
        
        
        async_route_handler = ASYNC_ROUTES.get((method, path))
        if async_route_handler:
            return asyncio.run(async_route_handler(event))
        

        return response_model(status_code=404, message={"error": "Route not found"})

    except Exception as e:
        return handle_exception(e)