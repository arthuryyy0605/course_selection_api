import json
from functools import wraps
from inspect import isclass
from fastapi.responses import JSONResponse
import json
import logging
import traceback
from enum import Enum
from functools import wraps
from typing import Any, Callable, List, Optional, Union

from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.params import Depends, Query
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel
from starlette.datastructures import QueryParams
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from course_selection_api.lib.logger import get_prefix_logger_adapter, logger


class SortOption(Enum):
    ASC = 'asc'
    DESC = 'desc'


class Sort(BaseModel):

    @staticmethod
    def create_sort(key_option):
        key_option_split = key_option.split(':')
        key = key_option_split[0]
        option = SortOption(key_option_split[1]) if len(
            key_option_split) > 1 else SortOption.ASC
        return Sort(key=key, option=option)

    def to_string(self):
        return f'{self.key}:{self.option.value}'

    key: str
    option: SortOption


class Page(BaseModel):
    page: int
    page_size: int


class PageFilter(Page):
    sort: List[Sort]

    def to_query_dict(self):
        query_dict = {'page': self.page,
                      'page_size': self.page_size,
                      'sort': [s.to_string() for s in self.sort]}
        return query_dict


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            error_stack = traceback.format_exc()

            logger.error(f"""
                Unhandled error occurred:
                Path: {request.url.path}
                Method: {request.method}
                Error: {str(e)}
                Stack: {error_stack}
            """)

            return JSONResponse(
                status_code=500,
                content={
                    "code": "500000",
                    "message": f"INTERNAL_ERROR {e}"
                }
            )


class HyException(Exception):
    message: str
    code: str

    def __init__(self, code: str, message: str):
        self.message = message
        self.code = code


def use_route_names_as_operation_ids(app: FastAPI):
    """
    Simplify operation IDs so that generated API clients have simpler function names.
    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


def depend_sort(sort_expression: Enum):
    def dependency(sort: Union[List[sort_expression], None] =
                   Query(default=None, description='Multi-selectable sorting')) -> List[Sort]:
        if sort:
            return [Sort.create_sort(s.value) for s in sort]
        else:
            return []

    return Depends(dependency)


def depend_page():
    def dependency(page: int = Query(default=1, ge=1),
                   page_size: int = Query(default=20, le=100, ge=1)) -> Page:
        return Page(page=page, page_size=page_size)

    return Depends(dependency)


def depend_page_and_sort(sort_expression: List[Sort]):
    def dependency(page: int = Query(default=1, ge=1),
                   page_size: int = Query(default=20, le=100, ge=1),
                   sort=depend_sort(sort_expression)) -> PageFilter:
        return PageFilter(page=page, page_size=page_size, sort=sort)

    return Depends(dependency)


def depend_optional_page():
    def dependency(page: int = Query(default=None),
                   page_size: int = Query(default=None)) -> Optional[Page]:
        if all([page, page_size]):
            return Page(page=page, page_size=page_size)
        elif any([page, page_size]):
            raise ValueError("Can't have only one value")
        else:
            return None

    return Depends(dependency)


def disable_uvicorn_logger():
    logging.getLogger("uvicorn.error").disabled = True
    logging.getLogger("uvicorn.access").disabled = True


def disable_mangum_logger():
    logging.getLogger("mangum").disabled = True
    logging.getLogger("mangum.lifespan").disabled = True


def to_json_response(response: Any):
    content = jsonable_encoder(response)
    return JSONResponse(content=content)


def hy_exception_to_json_response(hy_exc: HyException) -> JSONResponse:
    return JSONResponse(
        status_code=int(int(hy_exc.code) / 1000),
        content={"code": hy_exc.code, "message": hy_exc.message},
    )


def client_exception_to_json_response(exc) -> JSONResponse:
    error = json.loads(exc.body)
    error_code = error.get('code')
    return JSONResponse(
        status_code=exc.status,
        content={"code": error_code if error_code is not None else str(exc.status) + '000',
                 "message": error.get('message') if error_code else error.get('detail')},
    )


def add_exception_handler(app: FastAPI):
    @app.exception_handler(Exception)
    @error_log_handler
    async def all_exception_handler(request: Request, exc: Exception):
        return hy_exception_to_json_response(hy_exc=UnhandledException(message=str(exc)))

    @app.exception_handler(HyException)
    @error_log_handler
    async def hy_exception_handler(request: Request, exc: HyException):
        return hy_exception_to_json_response(hy_exc=exc)

    @app.exception_handler(RequestValidationError)
    @error_log_handler
    async def validation_exception_handler(request, exc: RequestValidationError):
        return hy_exception_to_json_response(hy_exc=ParameterViolationException(message=str(exc)))

    return app


logger_request = get_prefix_logger_adapter("api-request-log")
logger_response = get_prefix_logger_adapter("api-response-log")
logger_exception = get_prefix_logger_adapter("api-exception-log")


def _handle_query_parameter(query_params: QueryParams) -> dict:
    params_dict = {}
    for parameter_key in query_params.keys():
        value = query_params.getlist(parameter_key)
        params_dict[parameter_key] = value
    return params_dict


def get_response_log(api_response: Response) -> dict:
    response_body = None
    try:
        if (response_content_length := int(api_response.headers.get('content-length', 0))) > 1000:
            response_body = f'Response log failed, because response content length ({response_content_length}) > 1000'
        elif response_content_length > 0:
            response_body = json.loads(api_response.body)
    except Exception as e:
        logger_response.warning({'message': f"Record response failed: {e}"})

    return {
        'status_code': api_response.status_code,
        'response_body': response_body
    }


def error_log_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        response = await func(*args, **kwargs)
        exc_dict = json.loads(response.body)
        status_code = int(exc_dict['code'][:3])
        if status_code >= 500:
            logger_exception.error({'message': exc_dict})
        if 400 <= status_code < 500:
            logger_exception.warning({'message': exc_dict})
        return response

    return wrapper


def exception_mapping(handled_exception: type[Exception], raise_exception: tuple[HyException, type[HyException]],
                      extend_message: bool = False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except handled_exception as e:
                if isclass(raise_exception):
                    if extend_message:
                        raise raise_exception(message=str(e))
                    else:
                        raise raise_exception()
                else:
                    if extend_message:
                        raise_exception.message = str(e)
                    raise raise_exception

        return wrapper

    return decorator


class UnhandledException(HyException):
    def __init__(self, code: str = '500000', message: str = "Unhandled error:"):
        super().__init__(code, message)


class NotFoundException(HyException):
    def __init__(self, code: str = '404000', message: str = "Resource not found."):
        super().__init__(code, message)


class BadRequestException(HyException):
    def __init__(self, code: str = '400000', message: str = "Bad request."):
        super().__init__(code, message)


class ParameterViolationException(HyException):
    def __init__(self, code: str = '400700', message: str = "Parameter value is not valid； "):
        super().__init__(code, message)


class ForeignKeyViolationException(HyException):
    def __init__(self, code: str = '400701',
                 message: str = "Parameter value is not a valid member; permitted: .."):
        super().__init__(code, message)


class UniqueViolationException(HyException):
    def __init__(self, code: str = '400800', message: str = "The same key existed in the database.."):
        super().__init__(code, message)


class DuplicateEntityException(HyException):
    def __init__(self, code: str = '400900', message: str = "The same entity existed in the system.."):
        super().__init__(code, message)


class RestrictionException(HyException):
    def __init__(self, code: str = '409800', message: str = "This behavior is prohibited.."):
        super().__init__(code, message)


class UnauthorizedException(HyException):
    def __init__(self, code: str = '401000', message: str = "Unauthorized."):
        super().__init__(code, message)


class ForbiddenException(HyException):
    def __init__(self, code: str = '403000', message: str = "Forbidden."):
        super().__init__(code=code, message=message)


class ResourceNotFoundException(HyException):
    def __init__(self, code: str = '404001', message: str = "Resource not found."):
        super().__init__(code=code, message=message)


class RequestEntityTooLarge(HyException):
    def __init__(self, code: str = '413000', message: str = "The data value transmitted exceeds the capacity limit."):
        super().__init__(code=code, message=message)
