from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.access_admin import (
    PermissionResponse,
    RoleListResponse,
    RoleResponse,
    RoleUpsertRequest,
    UserListResponse,
    UserResponse,
    UserUpsertRequest,
)
from app.services.access_admin_service import AccessAdminService

router = APIRouter(prefix="/admin", tags=["admin-access"])


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(db: Session = Depends(db_session)) -> list[PermissionResponse]:
    service = AccessAdminService(db)
    return service.list_permissions()


@router.get("/roles", response_model=RoleListResponse)
def list_roles(db: Session = Depends(db_session)) -> RoleListResponse:
    service = AccessAdminService(db)
    return service.list_roles()


@router.post("/roles", response_model=RoleResponse)
def create_role(
    payload: RoleUpsertRequest,
    db: Session = Depends(db_session),
) -> RoleResponse:
    service = AccessAdminService(db)
    try:
        return service.create_role(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: str,
    payload: RoleUpsertRequest,
    db: Session = Depends(db_session),
) -> RoleResponse:
    service = AccessAdminService(db)
    try:
        return service.update_role(role_id=role_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/roles/{role_id}")
def delete_role(role_id: str, db: Session = Depends(db_session)) -> dict[str, str]:
    service = AccessAdminService(db)
    try:
        return service.delete_role(role_id=role_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/users", response_model=UserListResponse)
def list_users(
    q: str | None = Query(default=None),
    role_code: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> UserListResponse:
    service = AccessAdminService(db)
    return service.list_users(
        q=q,
        role_code=role_code,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.post("/users", response_model=UserResponse)
def create_user(
    payload: UserUpsertRequest,
    db: Session = Depends(db_session),
) -> UserResponse:
    service = AccessAdminService(db)
    try:
        return service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpsertRequest,
    db: Session = Depends(db_session),
) -> UserResponse:
    service = AccessAdminService(db)
    try:
        return service.update_user(user_id=user_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(db_session)) -> dict[str, str]:
    service = AccessAdminService(db)
    try:
        return service.delete_user(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
