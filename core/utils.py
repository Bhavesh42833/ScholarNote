import os
import requests
from core.logger import logger
from core.exceptions import jobProcessingError
from functools import wraps
import json

class youtube:
    def get_video_metadata(self, url):
        logger.info(f"Fetching video metadata for URL: {url}")
        api_url=f"https://www.youtube.com/oembed?url={url}&format=json"
        info=requests.get(api_url).json()
        if not info:
            logger.warning(f"No metadata found for URL: {url}")
            return {}
        
        return {
            "title": info.get("title") or "",
            "channel": info.get("author_name") or ""
        }
    
    def get_video_transcript(self, url):
        logger.info(f"Fetching video transcript for URL: {url}")
        # Placeholder for actual transcript fetching logic
        video_id = url.split("v=")[-1]
        api_url = os.environ.get("TRANSCRIPT_API_URL")
        modified_url = f"{api_url}?videoId={video_id}"
        transcript= requests.get(modified_url)
        return transcript.json()

def db_operation(message_func=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self,*args, **kwargs):
            try:
                result = func(self, *args, **kwargs)
                # dynamic message
                if message_func:
                    msg = message_func(self, *args, **kwargs)
                else:
                    msg = f"{func.__name__} executed"

                logger.info(msg)
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise e

        return wrapper
    return decorator


def response_model(status_code: int, message: dict=None, data: dict=None):
    logger.info(f"Event processed.Response sent.")
    return {
        "status_code": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": message,
            "data": data
        })
    }

