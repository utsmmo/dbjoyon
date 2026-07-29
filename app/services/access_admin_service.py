from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.access_admin_repository import AccessAdminRepository
from app.schemas.access_admin import (
    PermissionResponse,
    RoleListResponse,
    RoleResponse,
    RoleUpsertRequest,
    UserListResponse,
    UserResponse,
    UserUpsertRequest,
)


class AccessAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AccessAdminRepository(db)

    def list_permissions(self) -> list[PermissionResponse]:
        self.repository.ensure_access_baseline()
        self.db.commit()
        return [PermissionResponse(**item) for item in self.repository.list_permissions()]

    def list_roles(self) -> RoleListResponse:
        self.repository.ensure_access_baseline()
        self.db.commit()
        items = [RoleResponse(**item) for item in self.repository.list_roles()]
        return RoleListResponse(items=items, total=len(items))

    def create_role(self, payload: RoleUpsertRequest) -> RoleResponse:
        try:
            self.repository.ensure_access_baseline()
            role = self.repository.create_role(payload.model_dump(mode="json"))
            self.db.commit()
            return RoleResponse(**role)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("role code already exists or payload is invalid") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while creating role") from exc

    def update_role(self, *, role_id: str, payload: RoleUpsertRequest) -> RoleResponse:
        try:
            role = self.repository.update_role(
                role_id=role_id,
                payload=payload.model_dump(mode="json"),
            )
            if role is None:
                raise ValueError("role not found")
            self.db.commit()
            return RoleResponse(**role)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("role update contains duplicate or invalid data") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while updating role") from exc

    def delete_role(self, *, role_id: str) -> dict[str, str]:
        try:
            deleted = self.repository.delete_role(role_id=role_id)
            if not deleted:
                raise ValueError("role not found")
            self.db.commit()
            return {"deleted_role_id": role_id, "status": "success"}
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while deleting role") from exc

    def list_users(
        self,
        *,
        q: str | None,
        role_code: str | None,
        is_active: bool | None,
        limit: int,
        offset: int,
    ) -> UserListResponse:
        self.repository.ensure_access_baseline()
        self.db.commit()
        items, total = self.repository.list_users(
            q=q,
            role_code=role_code,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        return UserListResponse(
            items=[UserResponse(**item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def create_user(self, payload: UserUpsertRequest) -> UserResponse:
        if not payload.password:
            raise ValueError("password is required when creating user")
        try:
            self.repository.ensure_access_baseline()
            user = self.repository.create_user(payload.model_dump(mode="json"))
            self.db.commit()
            return UserResponse(**user)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("user email already exists or payload is invalid") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while creating user") from exc

    def update_user(self, *, user_id: str, payload: UserUpsertRequest) -> UserResponse:
        try:
            user = self.repository.update_user(
                user_id=user_id,
                payload=payload.model_dump(mode="json"),
            )
            if user is None:
                raise ValueError("user not found")
            self.db.commit()
            return UserResponse(**user)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("user update contains duplicate or invalid data") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while updating user") from exc

    def delete_user(self, *, user_id: str) -> dict[str, str]:
        try:
            deleted = self.repository.delete_user(user_id=user_id)
            if not deleted:
                raise ValueError("user not found")
            self.db.commit()
            return {"deleted_user_id": user_id, "status": "success"}
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while deleting user") from exc
