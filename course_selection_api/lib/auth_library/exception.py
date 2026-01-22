from ..base_exception import HyException


class LimitExceededException(HyException):
    def __init__(self, code: str = '400601', message: str = 'Attempt limit exceeded, please try after some time.'):
        super().__init__(code, message)


class InvalidUsernameOrPasswordException(HyException):
    def __init__(self, code: str = '401700', message: str = 'Invalid username or password.'):
        super().__init__(code, message)


class TokenExpiredException(HyException):
    def __init__(self, code: str = '401701', message: str = 'Token expired.'):
        super().__init__(code, message)


class UserNotExistException(HyException):
    def __init__(self, code: str = '401702', message: str = 'User not exist.'):
        super().__init__(code, message)


class DisabledUserException(HyException):
    def __init__(self, code: str = '401600', message: str = 'User has been disabled.'):
        super().__init__(code, message)


class NewPasswordRequiredException(HyException):
    def __init__(self, code: str = '401703', message: str = 'New password required.'):
        super().__init__(code, message)
