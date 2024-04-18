class BusinessException(Exception):
    """Exception raised for business-related errors."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
