import math
from pydantic import BaseModel, Field, computed_field


class PageResponse[T: BaseModel](BaseModel):
    items: list[T] = Field(
        ...,
        title="Items on this page",
        description="Items limited according to the pagination query settings",
    )
    total: int = Field(
        ...,
        ge=0,
        title="Total number of items",
        description="Number of items across all pages, before pagination is applied",
    )
    current_page: int = Field(..., ge=1, title="Current page number")
    per_page: int = Field(..., ge=1, title="Amount of items per page")
    next_page: str | None = Field(
        ...,
        title="Next page path",
        description="Null on the last page",
    )
    prev_page: str | None = Field(
        ...,
        title="Previous page path",
        description="Null on the first page",
    )
    first_page: str | None = Field(
        ...,
        title="First page path",
        description="Path of the first page with the current per_page value",
    )
    last_page: str | None = Field(
        ...,
        title="Last page path",
        description="Path of the last page with the current per_page value",
    )

    @computed_field(
        title="Total number of pages",
        description="Derived as ceil(total / per_page), so it cannot disagree with them",
    )
    @property
    def total_pages(self) -> int:
        return math.ceil(self.total / self.per_page)
