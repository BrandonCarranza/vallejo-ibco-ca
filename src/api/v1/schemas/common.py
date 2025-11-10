"""
Common Pydantic schemas used across multiple endpoints.
"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class DataSourceResponse(BaseModel):
    """Data source information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: str
    organization: str
    url: Optional[str] = None
    description: Optional[str] = None
    reliability_rating: Optional[str] = None
    access_method: str
    expected_update_frequency: Optional[str] = None
    last_checked_date: Optional[datetime] = None


class DataLineageResponse(BaseModel):
    """Data lineage information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_name: str
    record_id: int
    field_name: str
    source_document_url: Optional[str] = None
    source_document_page: Optional[int] = None
    extraction_method: str
    extracted_by: Optional[str] = None
    extracted_at: datetime
    validated: bool
    validated_by: Optional[str] = None
    confidence_level: Optional[str] = None
    notes: Optional[str] = None


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page")
    per_page: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
