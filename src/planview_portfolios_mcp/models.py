"""Pydantic models for input validation and type safety."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectCreate(BaseModel):
    """Validation model for project creation."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    portfolio_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectCreate":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")
        return self


class ProjectUpdate(BaseModel):
    """Validation model for project updates."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectUpdate":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")
        return self


class ResourceAllocation(BaseModel):
    """Validation model for resource allocation."""

    resource_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    allocation_percentage: float = Field(ge=0, le=100)
    start_date: date
    end_date: date
    role: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ResourceAllocation":
        if self.start_date >= self.end_date:
            raise ValueError("end_date must be after start_date")
        return self


class ListProjectsParams(BaseModel):
    """Validation for list_projects parameters."""

    portfolio_id: str | None = None
    status: str | None = None
    limit: int = Field(50, ge=1, le=1000)


class ListResourcesParams(BaseModel):
    """Validation for list_resources parameters."""

    department: str | None = None
    role: str | None = None
    available: bool | None = None
    limit: int = Field(50, ge=1, le=1000)


class ProjectResponse(BaseModel):
    """Typed response for project data."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str | None = None
    status: str | None = None
    portfolio_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResourceResponse(BaseModel):
    """Typed response for resource data."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    email: str | None = None
    department: str | None = None
    role: str | None = None
    capacity: float | None = None
    available: bool = True


class AllocationResponse(BaseModel):
    """Typed response for allocation data."""

    model_config = ConfigDict(extra="allow")

    id: str
    resource_id: str
    project_id: str
    allocation_percentage: float
    start_date: date
    end_date: date
    role: str | None = None
