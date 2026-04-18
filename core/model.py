from dataclasses import dataclass
from typing import Optional
from core.exceptions import jobValidationError
from core.logger import logger

@dataclass
class Job:
    session_id: str
    file_id: str
    file_type: str
    file_name: Optional[str] = None
    deleted_files: Optional[list] = None
    selected_file_ids: Optional[list] = None
    transcript: Optional[str] = None

    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None

    video_url: Optional[str] = None
    web_url: Optional[str] = None

    def __init__(self, **kwargs):
        self.session_id = kwargs.get("session_id")
        self.file_id = kwargs.get("file_id")
        self.file_type = kwargs.get("file_type")
        self.file_name = kwargs.get("file_name")
        self.video_url = kwargs.get("video_url", None)
        self.web_url = kwargs.get("web_url", None)
        self.deleted_files = kwargs.get("deleted_files", [])
        self.selected_file_ids = kwargs.get("selected_file_ids", [])
        self.s3_key = kwargs.get("s3_key", None)
        self.s3_bucket = kwargs.get("s3_bucket", None)
    
    def validate(self):
        logger.info(f"Validating job")
        if self.session_id is None:
            raise jobValidationError("session_id is required")
        if self.file_id is None:
            raise jobValidationError("file_id is required")
        if self.file_type is None:
            raise jobValidationError("file_type is required")
        if self.file_type.lower() not in ["pdf", "video","query", "web"]:
            raise jobValidationError("file_type must be either 'pdf', 'video', 'query', or 'web'")
        if self.file_type.lower() == "pdf":
            if self.file_name is None:
                raise jobValidationError("file_name is required for pdf type")
        if self.file_type.lower() == "video":
            if self.video_url is None:
                raise jobValidationError("video_url is required for video type")
        if self.file_type.lower() == "web":
            if self.web_url is None:
                raise jobValidationError("web_url is required for webpage type")
        if self.file_type.lower() == "query":
            if self.selected_file_ids is None or len(self.selected_file_ids) == 0:
                raise jobValidationError("selected_file_ids is required for query type")
        if self.s3_bucket is not None and self.s3_key is None:
            raise jobValidationError("s3_key is required if s3_bucket is provided")

    def is_pdf(self):
       return self.file_type.lower() == "pdf"
    
    def is_webpage(self):
       return self.file_type.lower() == "web"
    
    def get_deleted_files(self,db):
        self.deleted_files = db.get_deleted_files(job=self)
        
    