from core.exceptions import jobValidationError, jobProcessingError
from core.logger import logger
import json

def handle_exception(e: Exception):
    logger.error(f"An exception occurred: {str(e)}")
    if isinstance(e, jobValidationError):
        return {
        "body": json.dumps({"error": e.__class__.__name__, "message": e.message}),
        "status_code": e.status_code
        }
    elif isinstance(e, jobProcessingError):
        return {
            "body": json.dumps({"error": e.__class__.__name__, "message": e.message}),
            "status_code": e.status_code
            }
    else:
        return {
         "body": json.dumps({"error": "An unexpected error occurred: "+str(e)}),
         "status_code": 500
         }
