class ValidationError(Exception):
    """Исключение для бизнес-валидации"""

    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.message = message
        self.field = field
