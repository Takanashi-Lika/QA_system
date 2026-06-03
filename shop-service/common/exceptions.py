class ShopException(Exception):
    def __init__(self, code: int, message: str, http_status: int = 500):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class ValidationError(ShopException):
    def __init__(self, message: str = "参数校验失败"):
        super().__init__(code=40001, message=message, http_status=400)


class AuthenticationError(ShopException):
    def __init__(self, message: str = "未登录或Token过期"):
        super().__init__(code=40101, message=message, http_status=401)


class PermissionDeniedError(ShopException):
    def __init__(self, message: str = "无操作权限"):
        super().__init__(code=40301, message=message, http_status=403)


class NotFoundError(ShopException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=40401, message=message, http_status=404)


class BusinessError(ShopException):
    def __init__(self, message: str = "业务规则冲突"):
        super().__init__(code=42201, message=message, http_status=422)


class DatabaseError(ShopException):
    def __init__(self, message: str = "数据库异常"):
        super().__init__(code=50001, message=message, http_status=500)


class InternalError(ShopException):
    def __init__(self, message: str = "内部错误"):
        super().__init__(code=50002, message=message, http_status=500)
