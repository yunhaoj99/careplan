class BaseAppException(Exception):
    """
    All custom exceptions inherit from this.
    Front-end can always check response.type to decide what to do.
    """
    type = 'error'
    code = 'UNKNOWN_ERROR'
    default_message = 'An unexpected error occurred'
    http_status = 500

    def __init__(self, message=None, detail=None):
        self.message = message or self.default_message
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self):
        data = {
            'type': self.type,
            'code': self.code,
            'message': self.message,
        }
        if self.detail:
            data['detail'] = self.detail
        return data


class ValidationError(BaseAppException):
    type = 'validation_error'
    code = 'VALIDATION_ERROR'
    default_message = 'Validation failed'
    http_status = 400


class BlockError(BaseAppException):
    type = 'block'
    code = 'BLOCKED'
    default_message = 'Operation blocked by business rule'
    http_status = 409


class WarningException(BaseAppException):
    type = 'warning'
    code = 'WARNING'
    default_message = 'Potential issue detected'
    http_status = 200

    def __init__(self, warnings, message=None):
        self.warnings = warnings
        super().__init__(message or self.default_message)

    def to_dict(self):
        data = super().to_dict()
        data['warnings'] = self.warnings
        data['requires_confirmation'] = True
        return data
