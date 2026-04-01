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


def validate_task_key(v: str) -> str:
    """Validate task key URI format (key://, search://, ekey://)."""
    if not isinstance(v, str):
        raise ValueError("Task key must be a string")
    v = v.strip()
    if not v:
        raise ValueError("Task key cannot be empty")
    # Check for valid key URI formats
    if not (
        v.startswith("key://")
        or v.startswith("search://")
        or v.startswith("ekey://")
    ):
        raise ValueError(
            "Task key must be in key://, search://, or ekey:// format"
        )
    return v


class WorkOptionsDto(BaseModel):
    """Options for task operations."""

    copy_missing_values_from_planview: bool = Field(
        default=False, alias="CopyMissingValuesFromPlanview"
    )
    rollup_actuals: bool = Field(default=False, alias="RollupActuals")
    clear_staging_table_after_run: bool = Field(
        default=True, alias="ClearStagingTableAfterRun"
    )

    model_config = ConfigDict(populate_by_name=True)


class TaskDto2(BaseModel):
    """Task data transfer object for SOAP operations."""

    # Required fields (for create)
    description: str = Field(..., min_length=1, alias="Description")
    father_key: str = Field(..., alias="FatherKey")

    # Optional fields
    key: str | None = Field(None, alias="Key")
    schedule_start_date: datetime | None = Field(None, alias="ScheduleStartDate")
    schedule_finish_date: datetime | None = Field(
        None, alias="ScheduleFinishDate"
    )
    actual_start_date: datetime | None = Field(None, alias="ActualStartDate")
    actual_finish_date: datetime | None = Field(None, alias="ActualFinishDate")
    duration: int | None = Field(None, ge=0, alias="Duration")  # minutes
    calendar_key: str | None = Field(None, alias="CalendarKey")
    enter_progress: bool | None = Field(None, alias="EnterProgress")
    is_milestone: bool | None = Field(None, alias="IsMilestone")
    is_ticketable: bool | None = Field(None, alias="IsTicketable")
    is_deliverable: bool | None = Field(None, alias="IsDeliverable")
    percent_complete: int | None = Field(
        None, ge=0, le=100, alias="PercentComplete"
    )
    work_id: str | None = Field(None, alias="WorkId")
    work_status_key: str | None = Field(None, alias="WorkStatusKey")
    lifecycle_admin_user_key: str | None = Field(
        None, alias="LifecycleAdminUserKey"
    )
    notes: str | None = Field(None, alias="Notes")
    place: int | None = Field(None, ge=0, alias="Place")

    # Read-only fields (returned from API)
    depth: int | None = Field(None, alias="Depth", exclude=True)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",  # Allow extra fields from SOAP response
    )

    @model_validator(mode="after")
    def validate_task_dates(self) -> "TaskDto2":
        """Validate date relationships."""
        # If milestone, duration should be 0
        if self.is_milestone and self.duration is not None and self.duration != 0:
            raise ValueError("Milestones must have duration of 0")

        # Validate schedule dates
        if self.schedule_start_date and self.schedule_finish_date:
            if self.schedule_start_date > self.schedule_finish_date:
                raise ValueError(
                    "ScheduleStartDate cannot be after ScheduleFinishDate"
                )

        # Validate actual dates
        if self.actual_start_date and self.actual_finish_date:
            if self.actual_start_date > self.actual_finish_date:
                raise ValueError(
                    "ActualStartDate cannot be after ActualFinishDate"
                )

        return self


class TaskCreateRequest(BaseModel):
    """Input model for creating a task."""

    task: TaskDto2
    options: WorkOptionsDto | None = None


class TaskResponse(BaseModel):
    """Typed response for task data."""

    model_config = ConfigDict(extra="allow")

    key: str
    description: str
    father_key: str | None = None
    schedule_start_date: datetime | None = None
    schedule_finish_date: datetime | None = None
    actual_start_date: datetime | None = None
    actual_finish_date: datetime | None = None
    duration: int | None = None
    calendar_key: str | None = None
    enter_progress: bool | None = None
    is_milestone: bool | None = None
    is_ticketable: bool | None = None
    is_deliverable: bool | None = None
    percent_complete: int | None = None
    work_id: str | None = None
    work_status_key: str | None = None
    lifecycle_admin_user_key: str | None = None
    notes: str | None = None
    place: int | None = None
    depth: int | None = None
