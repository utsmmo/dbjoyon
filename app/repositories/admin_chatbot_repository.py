import json
import re
from uuid import UUID
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


SAFE_TARGET_REF_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_\.]*$")
DEFAULT_RAG_CHUNK_SIZE = 1200
DEFAULT_RAG_CHUNK_OVERLAP = 180


class AdminChatbotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_schema(self) -> None:
        self.db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS chatbot_hotel_bot_settings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    hotel_id UUID NOT NULL UNIQUE REFERENCES hotels(id) ON DELETE CASCADE,
                    bot_status VARCHAR(30) NOT NULL DEFAULT 'draft',
                    default_language VARCHAR(20) NOT NULL DEFAULT 'vi',
                    supported_languages JSONB NOT NULL DEFAULT '["vi"]'::jsonb,
                    confidence_threshold NUMERIC(5,4) NOT NULL DEFAULT 0.8500,
                    handoff_threshold NUMERIC(5,4) NOT NULL DEFAULT 0.6500,
                    allow_auto_reply BOOLEAN NOT NULL DEFAULT FALSE,
                    allow_after_hours_reply BOOLEAN NOT NULL DEFAULT TRUE,
                    allow_price_quote BOOLEAN NOT NULL DEFAULT FALSE,
                    allow_inventory_lookup BOOLEAN NOT NULL DEFAULT FALSE,
                    allow_booking_status_lookup BOOLEAN NOT NULL DEFAULT FALSE,
                    handoff_channel_code VARCHAR(100),
                    handoff_target_ref VARCHAR(255),
                    business_hours_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    notes TEXT,
                    updated_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT chk_chatbot_hotel_bot_status
                        CHECK (bot_status IN ('draft', 'pilot', 'active', 'paused'))
                )
                """
            )
        )
        self.db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS chatbot_knowledge_sources (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                    document_type VARCHAR(100) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    language VARCHAR(20) NOT NULL DEFAULT 'vi',
                    status VARCHAR(30) NOT NULL DEFAULT 'draft',
                    source_ref VARCHAR(255) NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    published_at TIMESTAMPTZ,
                    published_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    updated_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_chatbot_knowledge_sources UNIQUE (hotel_id, document_type, source_ref, version),
                    CONSTRAINT chk_chatbot_knowledge_source_status
                        CHECK (status IN ('draft', 'review', 'published', 'archived'))
                )
                """
            )
        )
        self.db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS chatbot_runtime_sources (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                    source_group VARCHAR(40) NOT NULL,
                    source_code VARCHAR(100) NOT NULL,
                    source_type VARCHAR(20) NOT NULL,
                    connection_name VARCHAR(100) NOT NULL,
                    target_ref VARCHAR(255) NOT NULL,
                    query_template TEXT,
                    mapping_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    last_checked_at TIMESTAMPTZ,
                    last_status VARCHAR(20) NOT NULL DEFAULT 'unknown',
                    last_error_message TEXT,
                    updated_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_chatbot_runtime_sources UNIQUE (hotel_id, source_group, source_code),
                    CONSTRAINT chk_chatbot_runtime_source_group
                        CHECK (source_group IN ('price', 'inventory', 'booking_status')),
                    CONSTRAINT chk_chatbot_runtime_source_type
                        CHECK (source_type IN ('table', 'view', 'api'))
                )
                """
            )
        )
        self.db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_chatbot_knowledge_sources_hotel_status
                    ON chatbot_knowledge_sources (hotel_id, status, updated_at DESC)
                """
            )
        )
        self.db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_chatbot_runtime_sources_group_status
                    ON chatbot_runtime_sources (source_group, last_status, last_checked_at DESC)
                """
            )
        )

    def list_hotel_bot_settings(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    h.id::text AS hotel_id,
                    h.hotel_name,
                    h.hotel_code,
                    COALESCE(s.bot_status, 'draft') AS bot_status,
                    COALESCE(s.default_language, 'vi') AS default_language,
                    COALESCE(s.supported_languages, '["vi"]'::jsonb) AS supported_languages,
                    COALESCE(s.confidence_threshold, 0.8500) AS confidence_threshold,
                    COALESCE(s.handoff_threshold, 0.6500) AS handoff_threshold,
                    COALESCE(s.allow_auto_reply, FALSE) AS allow_auto_reply,
                    COALESCE(s.allow_after_hours_reply, TRUE) AS allow_after_hours_reply,
                    COALESCE(s.allow_price_quote, FALSE) AS allow_price_quote,
                    COALESCE(s.allow_inventory_lookup, FALSE) AS allow_inventory_lookup,
                    COALESCE(s.allow_booking_status_lookup, FALSE) AS allow_booking_status_lookup,
                    s.handoff_channel_code,
                    s.handoff_target_ref,
                    COALESCE(s.business_hours_json, '{}'::jsonb) AS business_hours_json,
                    s.notes,
                    s.updated_by_user_id::text AS updated_by_user_id,
                    s.created_at,
                    s.updated_at
                FROM hotels h
                LEFT JOIN chatbot_hotel_bot_settings s ON s.hotel_id = h.id
                ORDER BY h.hotel_name ASC
                """
            )
        )
        return [dict(row) for row in rows.mappings().all()]

    def get_hotel_bot_settings(self, *, hotel_id: str) -> dict[str, Any] | None:
        self.db.execute(
            text(
                """
                INSERT INTO chatbot_hotel_bot_settings (hotel_id)
                VALUES (CAST(:hotel_id AS uuid))
                ON CONFLICT (hotel_id) DO NOTHING
                """
            ),
            {"hotel_id": hotel_id},
        )
        row = self.db.execute(
            text(
                """
                SELECT
                    h.id::text AS hotel_id,
                    h.hotel_name,
                    h.hotel_code,
                    s.bot_status,
                    s.default_language,
                    s.supported_languages,
                    s.confidence_threshold,
                    s.handoff_threshold,
                    s.allow_auto_reply,
                    s.allow_after_hours_reply,
                    s.allow_price_quote,
                    s.allow_inventory_lookup,
                    s.allow_booking_status_lookup,
                    s.handoff_channel_code,
                    s.handoff_target_ref,
                    s.business_hours_json,
                    s.notes,
                    s.updated_by_user_id::text AS updated_by_user_id,
                    s.created_at,
                    s.updated_at
                FROM chatbot_hotel_bot_settings s
                JOIN hotels h ON h.id = s.hotel_id
                WHERE s.hotel_id = CAST(:hotel_id AS uuid)
                """
            ),
            {"hotel_id": hotel_id},
        ).mappings().first()
        return dict(row) if row else None

    def update_hotel_bot_settings(self, *, hotel_id: str, payload: dict[str, Any], updated_by_user_id: str | None) -> dict[str, Any] | None:
        normalized_user_id = self._normalize_uuid(updated_by_user_id)
        self.db.execute(
            text(
                """
                INSERT INTO chatbot_hotel_bot_settings (hotel_id)
                VALUES (CAST(:hotel_id AS uuid))
                ON CONFLICT (hotel_id) DO NOTHING
                """
            ),
            {"hotel_id": hotel_id},
        )
        row = self.db.execute(
            text(
                """
                UPDATE chatbot_hotel_bot_settings
                SET
                    bot_status = :bot_status,
                    default_language = :default_language,
                    supported_languages = CAST(:supported_languages AS jsonb),
                    confidence_threshold = :confidence_threshold,
                    handoff_threshold = :handoff_threshold,
                    allow_auto_reply = :allow_auto_reply,
                    allow_after_hours_reply = :allow_after_hours_reply,
                    allow_price_quote = :allow_price_quote,
                    allow_inventory_lookup = :allow_inventory_lookup,
                    allow_booking_status_lookup = :allow_booking_status_lookup,
                    handoff_channel_code = :handoff_channel_code,
                    handoff_target_ref = :handoff_target_ref,
                    business_hours_json = CAST(:business_hours_json AS jsonb),
                    notes = :notes,
                    updated_by_user_id = :updated_by_user_id,
                    updated_at = NOW()
                WHERE hotel_id = CAST(:hotel_id AS uuid)
                RETURNING hotel_id::text
                """
            ),
            {
                "hotel_id": hotel_id,
                "bot_status": payload["bot_status"],
                "default_language": payload["default_language"],
                "supported_languages": json.dumps(payload["supported_languages"], ensure_ascii=True),
                "confidence_threshold": payload["confidence_threshold"],
                "handoff_threshold": payload["handoff_threshold"],
                "allow_auto_reply": payload["allow_auto_reply"],
                "allow_after_hours_reply": payload["allow_after_hours_reply"],
                "allow_price_quote": payload["allow_price_quote"],
                "allow_inventory_lookup": payload["allow_inventory_lookup"],
                "allow_booking_status_lookup": payload["allow_booking_status_lookup"],
                "handoff_channel_code": payload.get("handoff_channel_code"),
                "handoff_target_ref": payload.get("handoff_target_ref"),
                "business_hours_json": json.dumps(payload.get("business_hours_json") or {}, ensure_ascii=True),
                "notes": payload.get("notes"),
                "updated_by_user_id": normalized_user_id,
            },
        ).mappings().first()
        if row is None:
            return None
        return self.get_hotel_bot_settings(hotel_id=hotel_id)

    def list_knowledge_sources(
        self,
        *,
        hotel_id: str | None,
        document_type: str | None,
        status: str | None,
        language: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where_clauses = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if hotel_id:
            where_clauses.append("ks.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if document_type:
            where_clauses.append("ks.document_type = :document_type")
            params["document_type"] = document_type
        if status:
            where_clauses.append("ks.status = :status")
            params["status"] = status
        if language:
            where_clauses.append("ks.language = :language")
            params["language"] = language
        if q:
            where_clauses.append("(ks.title ILIKE :q OR ks.content ILIKE :q OR ks.source_ref ILIKE :q)")
            params["q"] = f"%{q}%"

        where_sql = " AND ".join(where_clauses)
        total = self.db.execute(
            text(
                f"""
                SELECT COUNT(*) AS total
                FROM chatbot_knowledge_sources ks
                WHERE {where_sql}
                """
            ),
            params,
        ).scalar_one()

        rows = self.db.execute(
            text(
                f"""
                SELECT
                    ks.id::text AS id,
                    ks.hotel_id::text AS hotel_id,
                    h.hotel_name,
                    h.hotel_code,
                    ks.document_type,
                    ks.title,
                    ks.content,
                    ks.language,
                    ks.status,
                    ks.source_ref,
                    ks.version,
                    ks.tags_json,
                    ks.metadata_json,
                    ks.published_at,
                    ks.published_by_user_id::text AS published_by_user_id,
                    doc.id::text AS synced_document_id,
                    sync_job.id::text AS last_sync_job_id,
                    sync_job.status AS last_sync_status,
                    sync_job.finished_at AS last_synced_at,
                    COALESCE(chunk_stats.chunk_count, 0) AS chunk_count,
                    ks.updated_by_user_id::text AS updated_by_user_id,
                    ks.created_at,
                    ks.updated_at
                FROM chatbot_knowledge_sources ks
                JOIN hotels h ON h.id = ks.hotel_id
                LEFT JOIN chatbot_knowledge_documents doc
                    ON doc.hotel_id = ks.hotel_id
                    AND doc.document_type = ks.document_type
                    AND doc.source_ref = ks.source_ref
                    AND doc.version = ks.version
                LEFT JOIN LATERAL (
                    SELECT j.id, j.status, j.finished_at
                    FROM chatbot_knowledge_sync_jobs j
                    WHERE j.source_name = 'chatbot_knowledge_sources'
                      AND j.input_ref = ks.id::text
                    ORDER BY j.created_at DESC
                    LIMIT 1
                ) sync_job ON TRUE
                LEFT JOIN LATERAL (
                    SELECT COUNT(*)::integer AS chunk_count
                    FROM chatbot_knowledge_chunks c
                    WHERE c.document_id = doc.id
                ) chunk_stats ON TRUE
                WHERE {where_sql}
                ORDER BY ks.updated_at DESC, ks.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        return [dict(row) for row in rows.mappings().all()], int(total or 0)

    def get_knowledge_source(self, *, source_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT
                    ks.id::text AS id,
                    ks.hotel_id::text AS hotel_id,
                    h.hotel_name,
                    h.hotel_code,
                    ks.document_type,
                    ks.title,
                    ks.content,
                    ks.language,
                    ks.status,
                    ks.source_ref,
                    ks.version,
                    ks.tags_json,
                    ks.metadata_json,
                    ks.published_at,
                    ks.published_by_user_id::text AS published_by_user_id,
                    doc.id::text AS synced_document_id,
                    sync_job.id::text AS last_sync_job_id,
                    sync_job.status AS last_sync_status,
                    sync_job.finished_at AS last_synced_at,
                    COALESCE(chunk_stats.chunk_count, 0) AS chunk_count,
                    ks.updated_by_user_id::text AS updated_by_user_id,
                    ks.created_at,
                    ks.updated_at
                FROM chatbot_knowledge_sources ks
                JOIN hotels h ON h.id = ks.hotel_id
                LEFT JOIN chatbot_knowledge_documents doc
                    ON doc.hotel_id = ks.hotel_id
                    AND doc.document_type = ks.document_type
                    AND doc.source_ref = ks.source_ref
                    AND doc.version = ks.version
                LEFT JOIN LATERAL (
                    SELECT j.id, j.status, j.finished_at
                    FROM chatbot_knowledge_sync_jobs j
                    WHERE j.source_name = 'chatbot_knowledge_sources'
                      AND j.input_ref = ks.id::text
                    ORDER BY j.created_at DESC
                    LIMIT 1
                ) sync_job ON TRUE
                LEFT JOIN LATERAL (
                    SELECT COUNT(*)::integer AS chunk_count
                    FROM chatbot_knowledge_chunks c
                    WHERE c.document_id = doc.id
                ) chunk_stats ON TRUE
                WHERE ks.id = CAST(:source_id AS uuid)
                """
            ),
            {"source_id": source_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_knowledge_source(self, payload: dict[str, Any], updated_by_user_id: str | None) -> dict[str, Any]:
        normalized_user_id = self._normalize_uuid(updated_by_user_id)
        row = self.db.execute(
            text(
                """
                INSERT INTO chatbot_knowledge_sources (
                    hotel_id,
                    document_type,
                    title,
                    content,
                    language,
                    status,
                    source_ref,
                    version,
                    tags_json,
                    metadata_json,
                    updated_by_user_id
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    :document_type,
                    :title,
                    :content,
                    :language,
                    :status,
                    :source_ref,
                    :version,
                    CAST(:tags_json AS jsonb),
                    CAST(:metadata_json AS jsonb),
                    :updated_by_user_id
                )
                RETURNING id::text AS id
                """
            ),
            {
                **payload,
                "tags_json": json.dumps(payload.get("tags_json") or [], ensure_ascii=True),
                "metadata_json": json.dumps(payload.get("metadata_json") or {}, ensure_ascii=True),
                "updated_by_user_id": normalized_user_id,
            },
        ).mappings().first()
        return self.get_knowledge_source(source_id=str(row["id"]))  # type: ignore[index]

    def update_knowledge_source(self, *, source_id: str, payload: dict[str, Any], updated_by_user_id: str | None) -> dict[str, Any] | None:
        normalized_user_id = self._normalize_uuid(updated_by_user_id)
        row = self.db.execute(
            text(
                """
                UPDATE chatbot_knowledge_sources
                SET
                    hotel_id = CAST(:hotel_id AS uuid),
                    document_type = :document_type,
                    title = :title,
                    content = :content,
                    language = :language,
                    status = :status,
                    source_ref = :source_ref,
                    version = :version,
                    tags_json = CAST(:tags_json AS jsonb),
                    metadata_json = CAST(:metadata_json AS jsonb),
                    updated_by_user_id = :updated_by_user_id,
                    updated_at = NOW()
                WHERE id = CAST(:source_id AS uuid)
                RETURNING id::text AS id
                """
            ),
            {
                **payload,
                "source_id": source_id,
                "tags_json": json.dumps(payload.get("tags_json") or [], ensure_ascii=True),
                "metadata_json": json.dumps(payload.get("metadata_json") or {}, ensure_ascii=True),
                "updated_by_user_id": normalized_user_id,
            },
        ).mappings().first()
        if row is None:
            return None
        return self.get_knowledge_source(source_id=source_id)

    def publish_knowledge_source(self, *, source_id: str, published_by_user_id: str | None) -> dict[str, Any] | None:
        normalized_user_id = self._normalize_uuid(published_by_user_id)
        row = self.db.execute(
            text(
                """
                UPDATE chatbot_knowledge_sources
                SET
                    status = 'published',
                    published_at = NOW(),
                    published_by_user_id = :published_by_user_id,
                    updated_by_user_id = :published_by_user_id,
                    updated_at = NOW()
                WHERE id = CAST(:source_id AS uuid)
                RETURNING id::text AS id
                """
            ),
            {
                "source_id": source_id,
                "published_by_user_id": normalized_user_id,
            },
        ).mappings().first()
        if row is None:
            return None
        return self.get_knowledge_source(source_id=source_id)

    def get_rag_chunk_config(self) -> tuple[int, int]:
        rows = self.db.execute(
            text(
                """
                SELECT setting_key, value_text
                FROM system_settings
                WHERE setting_key IN ('rag.chunk_size', 'rag.chunk_overlap')
                """
            )
        ).mappings().all()
        values = {str(row["setting_key"]): str(row["value_text"]) for row in rows}
        chunk_size = self._coerce_positive_int(values.get("rag.chunk_size"), DEFAULT_RAG_CHUNK_SIZE)
        chunk_overlap = self._coerce_positive_int(values.get("rag.chunk_overlap"), DEFAULT_RAG_CHUNK_OVERLAP)
        if chunk_overlap >= chunk_size:
            chunk_overlap = min(DEFAULT_RAG_CHUNK_OVERLAP, max(chunk_size - 50, 0))
        return chunk_size, chunk_overlap

    def create_knowledge_sync_job(
        self,
        *,
        hotel_id: str,
        source_ref: str,
        input_ref: str,
    ) -> str:
        row = self.db.execute(
            text(
                """
                INSERT INTO chatbot_knowledge_sync_jobs (
                    hotel_id,
                    job_type,
                    source_name,
                    source_ref,
                    status,
                    input_ref,
                    started_at,
                    created_at,
                    updated_at
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    'knowledge_sync',
                    'chatbot_knowledge_sources',
                    :source_ref,
                    'running',
                    :input_ref,
                    NOW(),
                    NOW(),
                    NOW()
                )
                RETURNING id::text AS id
                """
            ),
            {
                "hotel_id": hotel_id,
                "source_ref": source_ref,
                "input_ref": input_ref,
            },
        ).mappings().first()
        return str(row["id"])

    def complete_knowledge_sync_job(
        self,
        *,
        job_id: str,
        output_ref: str,
    ) -> None:
        self.db.execute(
            text(
                """
                UPDATE chatbot_knowledge_sync_jobs
                SET
                    status = 'done',
                    output_ref = :output_ref,
                    finished_at = NOW(),
                    updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {
                "job_id": job_id,
                "output_ref": output_ref,
            },
        )

    def fail_knowledge_sync_job(self, *, job_id: str, error_message: str) -> None:
        self.db.execute(
            text(
                """
                UPDATE chatbot_knowledge_sync_jobs
                SET
                    status = 'failed',
                    error_message = :error_message,
                    finished_at = NOW(),
                    updated_at = NOW()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {
                "job_id": job_id,
                "error_message": error_message,
            },
        )

    def upsert_knowledge_document_from_source(self, *, source: dict[str, Any]) -> str:
        row = self.db.execute(
            text(
                """
                INSERT INTO chatbot_knowledge_documents (
                    hotel_id,
                    document_type,
                    title,
                    language,
                    source,
                    source_ref,
                    content_raw,
                    version,
                    is_active,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    :document_type,
                    :title,
                    :language,
                    'admin_ui',
                    :source_ref,
                    :content_raw,
                    :version,
                    TRUE,
                    CAST(:metadata_json AS jsonb),
                    NOW(),
                    NOW()
                )
                ON CONFLICT (hotel_id, document_type, source_ref, version)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    language = EXCLUDED.language,
                    content_raw = EXCLUDED.content_raw,
                    is_active = TRUE,
                    metadata_json = EXCLUDED.metadata_json,
                    updated_at = NOW()
                RETURNING id::text AS id
                """
            ),
            {
                "hotel_id": str(source["hotel_id"]),
                "document_type": str(source["document_type"]),
                "title": str(source["title"]),
                "language": str(source["language"]),
                "source_ref": str(source["source_ref"]),
                "content_raw": str(source["content"]),
                "version": int(source["version"]),
                "metadata_json": json.dumps(
                    {
                        "source_table": "chatbot_knowledge_sources",
                        "source_id": str(source["id"]),
                        "tags": list(source.get("tags_json") or []),
                        "published_at": source.get("published_at").isoformat() if source.get("published_at") else None,
                        **dict(source.get("metadata_json") or {}),
                    },
                    ensure_ascii=True,
                ),
            },
        ).mappings().first()
        return str(row["id"])

    def replace_knowledge_chunks(
        self,
        *,
        document_id: str,
        hotel_id: str,
        language: str,
        tags: list[str],
        chunks: list[str],
    ) -> int:
        self.db.execute(
            text("DELETE FROM chatbot_knowledge_chunks WHERE document_id = CAST(:document_id AS uuid)"),
            {"document_id": document_id},
        )
        for index, chunk in enumerate(chunks, start=1):
            self.db.execute(
                text(
                    """
                    INSERT INTO chatbot_knowledge_chunks (
                        document_id,
                        hotel_id,
                        language,
                        chunk_order,
                        chunk_text,
                        vector_ref,
                        keywords,
                        metadata_json,
                        created_at
                    )
                    VALUES (
                        CAST(:document_id AS uuid),
                        CAST(:hotel_id AS uuid),
                        :language,
                        :chunk_order,
                        :chunk_text,
                        NULL,
                        CAST(:keywords AS jsonb),
                        CAST(:metadata_json AS jsonb),
                        NOW()
                    )
                    """
                ),
                {
                    "document_id": document_id,
                    "hotel_id": hotel_id,
                    "language": language,
                    "chunk_order": index,
                    "chunk_text": chunk,
                    "keywords": json.dumps(tags, ensure_ascii=True),
                    "metadata_json": json.dumps({"chunk_length": len(chunk)}, ensure_ascii=True),
                },
            )
        return len(chunks)

    def list_runtime_sources(self, *, hotel_id: str | None, source_group: str | None, is_active: bool | None) -> list[dict[str, Any]]:
        where_clauses = ["1=1"]
        params: dict[str, Any] = {}
        if hotel_id:
            where_clauses.append("rs.hotel_id = CAST(:hotel_id AS uuid)")
            params["hotel_id"] = hotel_id
        if source_group:
            where_clauses.append("rs.source_group = :source_group")
            params["source_group"] = source_group
        if is_active is not None:
            where_clauses.append("rs.is_active = :is_active")
            params["is_active"] = is_active

        rows = self.db.execute(
            text(
                f"""
                SELECT
                    rs.id::text AS id,
                    rs.hotel_id::text AS hotel_id,
                    h.hotel_name,
                    h.hotel_code,
                    rs.source_group,
                    rs.source_code,
                    rs.source_type,
                    rs.connection_name,
                    rs.target_ref,
                    rs.query_template,
                    rs.mapping_json,
                    rs.is_active,
                    rs.last_checked_at,
                    rs.last_status,
                    rs.last_error_message,
                    rs.updated_by_user_id::text AS updated_by_user_id,
                    rs.created_at,
                    rs.updated_at
                FROM chatbot_runtime_sources rs
                JOIN hotels h ON h.id = rs.hotel_id
                WHERE {" AND ".join(where_clauses)}
                ORDER BY h.hotel_name ASC, rs.source_group ASC, rs.source_code ASC
                """
            ),
            params,
        )
        return [dict(row) for row in rows.mappings().all()]

    def get_runtime_source(self, *, source_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            text(
                """
                SELECT
                    rs.id::text AS id,
                    rs.hotel_id::text AS hotel_id,
                    h.hotel_name,
                    h.hotel_code,
                    rs.source_group,
                    rs.source_code,
                    rs.source_type,
                    rs.connection_name,
                    rs.target_ref,
                    rs.query_template,
                    rs.mapping_json,
                    rs.is_active,
                    rs.last_checked_at,
                    rs.last_status,
                    rs.last_error_message,
                    rs.updated_by_user_id::text AS updated_by_user_id,
                    rs.created_at,
                    rs.updated_at
                FROM chatbot_runtime_sources rs
                JOIN hotels h ON h.id = rs.hotel_id
                WHERE rs.id = CAST(:source_id AS uuid)
                """
            ),
            {"source_id": source_id},
        ).mappings().first()
        return dict(row) if row else None

    def create_runtime_source(self, payload: dict[str, Any], updated_by_user_id: str | None) -> dict[str, Any]:
        normalized_user_id = self._normalize_uuid(updated_by_user_id)
        row = self.db.execute(
            text(
                """
                INSERT INTO chatbot_runtime_sources (
                    hotel_id,
                    source_group,
                    source_code,
                    source_type,
                    connection_name,
                    target_ref,
                    query_template,
                    mapping_json,
                    is_active,
                    updated_by_user_id
                )
                VALUES (
                    CAST(:hotel_id AS uuid),
                    :source_group,
                    :source_code,
                    :source_type,
                    :connection_name,
                    :target_ref,
                    :query_template,
                    CAST(:mapping_json AS jsonb),
                    :is_active,
                    :updated_by_user_id
                )
                RETURNING id::text AS id
                """
            ),
            {
                **payload,
                "mapping_json": json.dumps(payload.get("mapping_json") or {}, ensure_ascii=True),
                "updated_by_user_id": normalized_user_id,
            },
        ).mappings().first()
        return self.get_runtime_source(source_id=str(row["id"]))  # type: ignore[index]

    def update_runtime_source(self, *, source_id: str, payload: dict[str, Any], updated_by_user_id: str | None) -> dict[str, Any] | None:
        normalized_user_id = self._normalize_uuid(updated_by_user_id)
        row = self.db.execute(
            text(
                """
                UPDATE chatbot_runtime_sources
                SET
                    hotel_id = CAST(:hotel_id AS uuid),
                    source_group = :source_group,
                    source_code = :source_code,
                    source_type = :source_type,
                    connection_name = :connection_name,
                    target_ref = :target_ref,
                    query_template = :query_template,
                    mapping_json = CAST(:mapping_json AS jsonb),
                    is_active = :is_active,
                    updated_by_user_id = :updated_by_user_id,
                    updated_at = NOW()
                WHERE id = CAST(:source_id AS uuid)
                RETURNING id::text AS id
                """
            ),
            {
                **payload,
                "source_id": source_id,
                "mapping_json": json.dumps(payload.get("mapping_json") or {}, ensure_ascii=True),
                "updated_by_user_id": normalized_user_id,
            },
        ).mappings().first()
        if row is None:
            return None
        return self.get_runtime_source(source_id=source_id)

    def mark_runtime_source_test(self, *, source_id: str, status: str, error_message: str | None = None) -> dict[str, Any] | None:
        self.db.execute(
            text(
                """
                UPDATE chatbot_runtime_sources
                SET
                    last_checked_at = NOW(),
                    last_status = :status,
                    last_error_message = :error_message,
                    updated_at = NOW()
                WHERE id = CAST(:source_id AS uuid)
                """
            ),
            {
                "source_id": source_id,
                "status": status,
                "error_message": error_message,
            },
        )
        return self.get_runtime_source(source_id=source_id)

    def can_select_from_target_ref(self, target_ref: str) -> bool:
        return bool(SAFE_TARGET_REF_PATTERN.match(target_ref))

    def select_target_sample(self, *, target_ref: str) -> dict[str, Any] | None:
        result = self.db.execute(text(f"SELECT * FROM {target_ref} LIMIT 1"))
        row = result.mappings().first()
        return dict(row) if row else {}

    def _normalize_uuid(self, value: str | None) -> str | None:
        if not value:
            return None
        return str(UUID(value.strip()))

    def _coerce_positive_int(self, value: str | None, default: int) -> int:
        if value is None:
            return default
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default
