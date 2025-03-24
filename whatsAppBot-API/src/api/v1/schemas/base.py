from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 10

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    items: List[T]
    page: int
    pages: int
    has_next: bool
    has_prev: bool 