from collections import defaultdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


DEFAULT_ROLE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "code": "admin",
        "name": "Administrator",
        "description": "Toan quyen quan tri he thong",
        "permissions": [
            "dashboard.view",
            "hotel.view",
            "hotel.edit",
            "review.view",
            "review.edit",
            "review.reply",
            "user.view",
            "user.manage",
            "role.view",
            "role.manage",
            "settings.view",
            "settings.manage",
            "sales.view",
        ],
    },
    {
        "code": "manager",
        "name": "Manager",
        "description": "Quan ly hotel, review va team duoc giao",
        "permissions": [
            "dashboard.view",
            "hotel.view",
            "hotel.edit",
            "review.view",
            "review.edit",
            "review.reply",
            "user.view",
            "sales.view",
        ],
    },
    {
        "code": "member",
        "name": "Member",
        "description": "Nhan su van hanh co quyen xem co ban",
        "permissions": [
            "dashboard.view",
            "hotel.view",
            "review.view",
        ],
    },
    {
        "code": "sale",
        "name": "Sale",
        "description": "Nhan su sale xem hotel, dashboard va review lien quan",
        "permissions": [
            "dashboard.view",
            "hotel.view",
            "review.view",
            "sales.view",
        ],
    },
]

DEFAULT_PERMISSION_DEFINITIONS: list[dict[str, str]] = [
    {"code": "dashboard.view", "name": "View dashboard", "description": "Xem dashboard tong quan"},
    {"code": "hotel.view", "name": "View hotel", "description": "Xem thong tin khach san"},
    {"code": "hotel.edit", "name": "Edit hotel", "description": "Chinh sua thong tin khach san"},
    {"code": "review.view", "name": "View review", "description": "Xem review"},
    {"code": "review.edit", "name": "Edit review", "description": "Cap nhat metadata review"},
    {"code": "review.reply", "name": "Reply review", "description": "Quan ly phan hoi review"},
    {"code": "user.view", "name": "View user", "description": "Xem danh sach user"},
    {"code": "user.manage", "name": "Manage user", "description": "Them sua xoa user"},
    {"code": "role.view", "name": "View role", "description": "Xem vai tro va quyen"},
    {"code": "role.manage", "name": "Manage role", "description": "Them sua xoa role"},
    {"code": "settings.view", "name": "View settings", "description": "Xem cau hinh he thong"},
    {"code": "settings.manage", "name": "Manage settings", "description": "Quan ly cau hinh he thong"},
    {"code": "sales.view", "name": "View sales", "description": "Xem tinh nang danh cho sale"},
]


class AccessAdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_access_baseline(self) -> None:
        for permission in DEFAULT_PERMISSION_DEFINITIONS:
            self.db.execute(
                text(
                    """
                    INSERT INTO permissions (code, name, description)
                    VALUES (:code, :name, :description)
                    ON CONFLICT (code) DO NOTHING
                    """
                ),
                permission,
            )

        for role in DEFAULT_ROLE_DEFINITIONS:
            self.db.execute(
                text(
                    """
                    INSERT INTO roles (code, name, description, is_active)
                    VALUES (:code, :name, :description, TRUE)
                    ON CONFLICT (code) DO NOTHING
                    """
                ),
                {
                    "code": role["code"],
                    "name": role["name"],
                    "description": role["description"],
                },
            )

        for role in DEFAULT_ROLE_DEFINITIONS:
            for permission_code in role["permissions"]:
                self.db.execute(
                    text(
                        """
                        INSERT INTO role_permissions (role_id, permission_id)
                        SELECT r.id, p.id
                        FROM roles r
                        JOIN permissions p ON p.code = :permission_code
                        WHERE r.code = :role_code
                        ON CONFLICT (role_id, permission_id) DO NOTHING
                        """
                    ),
                    {
                        "role_code": role["code"],
                        "permission_code": permission_code,
                    },
                )

    def list_permissions(self) -> list[dict[str, Any]]:
        result = self.db.execute(
            text(
                """
                SELECT
                    id::text AS id,
                    code,
                    name,
                    description
                FROM permissions
                ORDER BY code ASC
                """
            )
        )
        return [dict(row) for row in result.mappings().all()]

    def list_roles(self) -> list[dict[str, Any]]:
        result = self.db.execute(
            text(
                """
                SELECT
                    r.id::text AS role_id,
                    r.code,
                    r.name,
                    r.description,
                    r.is_active,
                    r.created_at,
                    r.updated_at,
                    p.id::text AS permission_id,
                    p.code AS permission_code,
                    p.name AS permission_name,
                    p.description AS permission_description
                FROM roles r
                LEFT JOIN role_permissions rp ON rp.role_id = r.id
                LEFT JOIN permissions p ON p.id = rp.permission_id
                ORDER BY r.code ASC, p.code ASC
                """
            )
        )
        rows = result.mappings().all()
        grouped: dict[str, dict[str, Any]] = {}

        for row in rows:
            role_id = row["role_id"]
            if role_id not in grouped:
                grouped[role_id] = {
                    "id": role_id,
                    "code": row["code"],
                    "name": row["name"],
                    "description": row["description"],
                    "is_active": row["is_active"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "permissions": [],
                }
            if row["permission_id"]:
                grouped[role_id]["permissions"].append(
                    {
                        "id": row["permission_id"],
                        "code": row["permission_code"],
                        "name": row["permission_name"],
                        "description": row["permission_description"],
                    }
                )
        return list(grouped.values())

    def create_role(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.db.execute(
            text(
                """
                INSERT INTO roles (code, name, description, is_active)
                VALUES (:code, :name, :description, :is_active)
                RETURNING id::text AS id
                """
            ),
            payload,
        )
        role_id = result.scalar_one()
        self.replace_role_permissions(role_id=role_id, permission_codes=payload["permission_codes"])
        return self.get_role(role_id=role_id)

    def update_role(self, *, role_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        result = self.db.execute(
            text(
                """
                UPDATE roles
                SET
                    code = :code,
                    name = :name,
                    description = :description,
                    is_active = :is_active,
                    updated_at = NOW()
                WHERE id = CAST(:role_id AS uuid)
                RETURNING id::text AS id
                """
            ),
            {"role_id": role_id, **payload},
        )
        updated_id = result.scalar()
        if not updated_id:
            return None
        self.replace_role_permissions(role_id=role_id, permission_codes=payload["permission_codes"])
        return self.get_role(role_id=role_id)

    def delete_role(self, *, role_id: str) -> bool:
        result = self.db.execute(
            text(
                """
                DELETE FROM roles
                WHERE id = CAST(:role_id AS uuid)
                RETURNING id
                """
            ),
            {"role_id": role_id},
        )
        return result.first() is not None

    def get_role(self, *, role_id: str) -> dict[str, Any] | None:
        roles = self.db.execute(
            text(
                """
                SELECT
                    r.id::text AS role_id,
                    r.code,
                    r.name,
                    r.description,
                    r.is_active,
                    r.created_at,
                    r.updated_at,
                    p.id::text AS permission_id,
                    p.code AS permission_code,
                    p.name AS permission_name,
                    p.description AS permission_description
                FROM roles r
                LEFT JOIN role_permissions rp ON rp.role_id = r.id
                LEFT JOIN permissions p ON p.id = rp.permission_id
                WHERE r.id = CAST(:role_id AS uuid)
                ORDER BY p.code ASC
                """
            ),
            {"role_id": role_id},
        ).mappings().all()
        if not roles:
            return None
        first = roles[0]
        return {
            "id": first["role_id"],
            "code": first["code"],
            "name": first["name"],
            "description": first["description"],
            "is_active": first["is_active"],
            "created_at": first["created_at"],
            "updated_at": first["updated_at"],
            "permissions": [
                {
                    "id": row["permission_id"],
                    "code": row["permission_code"],
                    "name": row["permission_name"],
                    "description": row["permission_description"],
                }
                for row in roles
                if row["permission_id"]
            ],
        }

    def replace_role_permissions(self, *, role_id: str, permission_codes: list[str]) -> None:
        self.db.execute(
            text(
                """
                DELETE FROM role_permissions
                WHERE role_id = CAST(:role_id AS uuid)
                """
            ),
            {"role_id": role_id},
        )
        for permission_code in permission_codes:
            self.db.execute(
                text(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT CAST(:role_id AS uuid), p.id
                    FROM permissions p
                    WHERE p.code = :permission_code
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                    """
                ),
                {
                    "role_id": role_id,
                    "permission_code": permission_code,
                },
            )

    def list_users(
        self,
        *,
        q: str | None,
        role_code: str | None,
        is_active: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if q:
            filters.append("(u.email ILIKE :q OR u.full_name ILIKE :q)")
            params["q"] = f"%{q}%"
        if is_active is not None:
            filters.append("u.is_active = :is_active")
            params["is_active"] = is_active
        if role_code:
            filters.append(
                """
                EXISTS (
                    SELECT 1
                    FROM user_roles urf
                    JOIN roles rf ON rf.id = urf.role_id
                    WHERE urf.user_id = u.id AND rf.code = :role_code
                )
                """
            )
            params["role_code"] = role_code

        where_clause = " AND ".join(filters)
        total = int(
            self.db.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM users u
                    WHERE {where_clause}
                    """
                ),
                params,
            ).scalar_one()
        )
        result = self.db.execute(
            text(
                f"""
                SELECT
                    u.id::text AS user_id,
                    u.email,
                    u.full_name,
                    u.is_active,
                    u.created_at,
                    u.updated_at,
                    r.id::text AS role_id,
                    r.code AS role_code,
                    r.name AS role_name,
                    hs.hotel_id::text AS hotel_id
                FROM users u
                LEFT JOIN user_roles ur ON ur.user_id = u.id
                LEFT JOIN roles r ON r.id = ur.role_id
                LEFT JOIN user_hotel_scopes hs ON hs.user_id = u.id
                WHERE {where_clause}
                ORDER BY u.created_at DESC, r.code ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        rows = result.mappings().all()
        grouped: dict[str, dict[str, Any]] = {}
        role_seen: dict[str, set[str]] = defaultdict(set)
        hotel_seen: dict[str, set[str]] = defaultdict(set)

        for row in rows:
            user_id = row["user_id"]
            if user_id not in grouped:
                grouped[user_id] = {
                    "id": user_id,
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "is_active": row["is_active"],
                    "roles": [],
                    "hotel_ids": [],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            if row["role_id"] and row["role_id"] not in role_seen[user_id]:
                grouped[user_id]["roles"].append(
                    {
                        "id": row["role_id"],
                        "code": row["role_code"],
                        "name": row["role_name"],
                    }
                )
                role_seen[user_id].add(row["role_id"])
            if row["hotel_id"] and row["hotel_id"] not in hotel_seen[user_id]:
                grouped[user_id]["hotel_ids"].append(row["hotel_id"])
                hotel_seen[user_id].add(row["hotel_id"])
        return list(grouped.values()), total

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.db.execute(
            text(
                """
                INSERT INTO users (
                    email,
                    password_hash,
                    full_name,
                    is_active
                )
                VALUES (
                    :email,
                    crypt(:password, gen_salt('bf', 12)),
                    :full_name,
                    :is_active
                )
                RETURNING id::text AS id
                """
            ),
            payload,
        )
        user_id = result.scalar_one()
        self.replace_user_roles(user_id=user_id, role_codes=payload["role_codes"])
        self.replace_user_hotel_scopes(user_id=user_id, hotel_ids=payload["hotel_ids"])
        return self.get_user(user_id=user_id)

    def update_user(self, *, user_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        if payload.get("password"):
            result = self.db.execute(
                text(
                    """
                    UPDATE users
                    SET
                        email = :email,
                        password_hash = crypt(:password, gen_salt('bf', 12)),
                        full_name = :full_name,
                        is_active = :is_active,
                        updated_at = NOW()
                    WHERE id = CAST(:user_id AS uuid)
                    RETURNING id::text AS id
                    """
                ),
                {"user_id": user_id, **payload},
            )
        else:
            result = self.db.execute(
                text(
                    """
                    UPDATE users
                    SET
                        email = :email,
                        full_name = :full_name,
                        is_active = :is_active,
                        updated_at = NOW()
                    WHERE id = CAST(:user_id AS uuid)
                    RETURNING id::text AS id
                    """
                ),
                {"user_id": user_id, **payload},
            )
        updated_id = result.scalar()
        if not updated_id:
            return None
        self.replace_user_roles(user_id=user_id, role_codes=payload["role_codes"])
        self.replace_user_hotel_scopes(user_id=user_id, hotel_ids=payload["hotel_ids"])
        return self.get_user(user_id=user_id)

    def delete_user(self, *, user_id: str) -> bool:
        result = self.db.execute(
            text(
                """
                DELETE FROM users
                WHERE id = CAST(:user_id AS uuid)
                RETURNING id
                """
            ),
            {"user_id": user_id},
        )
        return result.first() is not None

    def get_user(self, *, user_id: str) -> dict[str, Any] | None:
        users, _ = self.list_users(q=None, role_code=None, is_active=None, limit=500, offset=0)
        return next((item for item in users if item["id"] == user_id), None)

    def replace_user_roles(self, *, user_id: str, role_codes: list[str]) -> None:
        self.db.execute(
            text(
                """
                DELETE FROM user_roles
                WHERE user_id = CAST(:user_id AS uuid)
                """
            ),
            {"user_id": user_id},
        )
        for role_code in role_codes:
            self.db.execute(
                text(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    SELECT CAST(:user_id AS uuid), r.id
                    FROM roles r
                    WHERE r.code = :role_code
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """
                ),
                {"user_id": user_id, "role_code": role_code},
            )

    def replace_user_hotel_scopes(self, *, user_id: str, hotel_ids: list[str]) -> None:
        self.db.execute(
            text(
                """
                DELETE FROM user_hotel_scopes
                WHERE user_id = CAST(:user_id AS uuid)
                """
            ),
            {"user_id": user_id},
        )
        for hotel_id in hotel_ids:
            self.db.execute(
                text(
                    """
                    INSERT INTO user_hotel_scopes (
                        user_id,
                        hotel_id,
                        can_view,
                        can_edit_reviews,
                        can_edit_hotel
                    )
                    VALUES (
                        CAST(:user_id AS uuid),
                        CAST(:hotel_id AS uuid),
                        TRUE,
                        FALSE,
                        FALSE
                    )
                    ON CONFLICT (user_id, hotel_id) DO NOTHING
                    """
                ),
                {"user_id": user_id, "hotel_id": hotel_id},
            )
