from datetime import datetime

from pydantic import BaseModel, Field


class PermissionResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None


class RoleUpsertRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    is_active: bool = True
    permission_codes: list[str] = Field(default_factory=list)


class RoleResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    is_active: bool
    permissions: list[PermissionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    items: list[RoleResponse]
    total: int


class UserRoleSummary(BaseModel):
    id: str
    code: str
    name: str


class UserUpsertRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=255)
    is_active: bool = True
    role_codes: list[str] = Field(default_factory=list)
    hotel_ids: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    roles: list[UserRoleSummary] = Field(default_factory=list)
    hotel_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    limit: int
    offset: int
