
class Error(Exception):
    def __init__(self,message,status_code=500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class jobValidationError(Error):
    def __init__(self,message):
        super().__init__(message, status_code=400)

class jobProcessingError(Error):
    def __init__(self,message):
        super().__init__(message, status_code=500)
