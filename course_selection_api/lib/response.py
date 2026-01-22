import math
from enum import Enum
from typing import Generic, List, Optional, TypeVar, Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel as GenericModel

from .base_exception import Page

STATUS = TypeVar('STATUS', bound=Enum)

RESULT = TypeVar('RESULT')


class ExceptionResponse(GenericModel):
    message: str
    code: str


class SingleResponse(GenericModel, Generic[RESULT]):
    result: RESULT


class ListResponse(GenericModel, Generic[RESULT]):
    result: List[RESULT]


class TotalResponse(GenericModel, Generic[RESULT]):
    total: int
    result: List[RESULT]


class PageResponse(GenericModel, Generic[RESULT]):
    page: int
    total_pages: int
    page_size: int
    total: int
    result: List[RESULT]

    @staticmethod
    def create(page: int, page_size: int, total: int, result: List[RESULT]):
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PageResponse(page=page, total_pages=total_pages, page_size=page_size, total=total, result=result)

    @staticmethod
    def of(total: int, result: List[RESULT], page: Optional[Page]):
        if page:
            page, page_size = page.dict().values()
        else:
            page, page_size = 1, total
        return PageResponse.create(page=page, page_size=page_size, total=total, result=result)


def to_json_response(response: Any):
    content = jsonable_encoder(response)
    return JSONResponse(content=content)
