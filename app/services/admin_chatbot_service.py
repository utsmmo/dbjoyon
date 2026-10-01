from datetime import datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.admin_chatbot_repository import AdminChatbotRepository
from app.schemas.admin_chatbot import (
    ChatbotHotelSettingsListResponse,
    ChatbotHotelSettingsResponse,
    ChatbotHotelSettingsUpdateRequest,
    ChatbotKnowledgePublishRequest,
    ChatbotKnowledgeSyncRequest,
    ChatbotKnowledgeSyncResponse,
    ChatbotKnowledgeSourceListResponse,
    ChatbotKnowledgeSourceResponse,
    ChatbotKnowledgeSourceUpsertRequest,
    ChatbotRuntimeSourceListResponse,
    ChatbotRuntimeSourceResponse,
    ChatbotRuntimeSourceTestResponse,
    ChatbotRuntimeSourceUpsertRequest,
)


class AdminChatbotService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AdminChatbotRepository(db)

    def list_hotel_settings(self) -> ChatbotHotelSettingsListResponse:
        try:
            self.repository.ensure_schema()
            items = [self._serialize_hotel_settings(item) for item in self.repository.list_hotel_bot_settings()]
            self.db.commit()
            return ChatbotHotelSettingsListResponse(items=items, total=len(items))
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while loading chatbot hotel settings") from exc

    def get_hotel_settings(self, *, hotel_id: str) -> ChatbotHotelSettingsResponse:
        try:
            self.repository.ensure_schema()
            item = self.repository.get_hotel_bot_settings(hotel_id=hotel_id)
            if item is None:
                raise ValueError("hotel not found")
            self.db.commit()
            return self._serialize_hotel_settings(item)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while loading hotel chatbot settings") from exc

    def update_hotel_settings(self, *, hotel_id: str, payload: ChatbotHotelSettingsUpdateRequest) -> ChatbotHotelSettingsResponse:
        if payload.handoff_threshold > payload.confidence_threshold:
            raise ValueError("handoff_threshold must be less than or equal to confidence_threshold")
        languages = [language.strip() for language in payload.supported_languages if language.strip()]
        if not languages:
            raise ValueError("supported_languages must contain at least one language")

        try:
            self.repository.ensure_schema()
            item = self.repository.update_hotel_bot_settings(
                hotel_id=hotel_id,
                payload={**payload.model_dump(mode="json"), "supported_languages": languages},
                updated_by_user_id=payload.updated_by_user_id,
            )
            if item is None:
                raise ValueError("hotel settings not found")
            self.db.commit()
            return self._serialize_hotel_settings(item)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while updating chatbot hotel settings") from exc

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
    ) -> ChatbotKnowledgeSourceListResponse:
        try:
            self.repository.ensure_schema()
            items, total = self.repository.list_knowledge_sources(
                hotel_id=hotel_id,
                document_type=document_type,
                status=status,
                language=language,
                q=q,
                limit=limit,
                offset=offset,
            )
            self.db.commit()
            return ChatbotKnowledgeSourceListResponse(
                items=[self._serialize_knowledge_source(item) for item in items],
                total=total,
                limit=limit,
                offset=offset,
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while loading chatbot knowledge sources") from exc

    def create_knowledge_source(self, payload: ChatbotKnowledgeSourceUpsertRequest) -> ChatbotKnowledgeSourceResponse:
        try:
            self.repository.ensure_schema()
            item = self.repository.create_knowledge_source(
                payload.model_dump(mode="json"),
                payload.updated_by_user_id,
            )
            self.db.commit()
            return self._serialize_knowledge_source(item)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("knowledge source already exists for this hotel, document_type, source_ref, and version") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while creating chatbot knowledge source") from exc

    def update_knowledge_source(self, *, source_id: str, payload: ChatbotKnowledgeSourceUpsertRequest) -> ChatbotKnowledgeSourceResponse:
        try:
            self.repository.ensure_schema()
            item = self.repository.update_knowledge_source(
                source_id=source_id,
                payload=payload.model_dump(mode="json"),
                updated_by_user_id=payload.updated_by_user_id,
            )
            if item is None:
                raise ValueError("knowledge source not found")
            self.db.commit()
            return self._serialize_knowledge_source(item)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("knowledge source already exists for this hotel, document_type, source_ref, and version") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while updating chatbot knowledge source") from exc

    def publish_knowledge_source(self, *, source_id: str, payload: ChatbotKnowledgePublishRequest) -> ChatbotKnowledgeSourceResponse:
        try:
            self.repository.ensure_schema()
            item = self.repository.publish_knowledge_source(
                source_id=source_id,
                published_by_user_id=payload.published_by_user_id,
            )
            if item is None:
                raise ValueError("knowledge source not found")
            self.db.commit()
            return self._serialize_knowledge_source(item)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while publishing chatbot knowledge source") from exc

    def sync_knowledge_source(self, *, source_id: str, payload: ChatbotKnowledgeSyncRequest) -> ChatbotKnowledgeSyncResponse:
        job_id: str | None = None
        try:
            self.repository.ensure_schema()
            source = self.repository.get_knowledge_source(source_id=source_id)
            if source is None:
                raise ValueError("knowledge source not found")
            if str(source["status"]) != "published":
                raise ValueError("knowledge source must be published before sync")

            job_id = self.repository.create_knowledge_sync_job(
                hotel_id=str(source["hotel_id"]),
                source_ref=str(source["source_ref"]),
                input_ref=str(source["id"]),
            )
            document_id = self.repository.upsert_knowledge_document_from_source(source=source)
            chunk_size, chunk_overlap = self.repository.get_rag_chunk_config()
            chunks = self._chunk_text(str(source["content"]), chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            if not chunks:
                chunks = [str(source["content"]).strip()]
            chunk_count = self.repository.replace_knowledge_chunks(
                document_id=document_id,
                hotel_id=str(source["hotel_id"]),
                language=str(source["language"]),
                tags=list(source.get("tags_json") or []),
                chunks=chunks,
            )
            self.repository.complete_knowledge_sync_job(job_id=job_id, output_ref=document_id)
            refreshed = self.repository.get_knowledge_source(source_id=source_id)
            synced_at = refreshed.get("last_synced_at") if refreshed else datetime.now().astimezone()
            self.db.commit()
            return ChatbotKnowledgeSyncResponse(
                job_id=job_id,
                source_id=source_id,
                document_id=document_id,
                chunk_count=chunk_count,
                status="done",
                synced_at=synced_at if isinstance(synced_at, datetime) else datetime.now().astimezone(),
            )
        except ValueError:
            if job_id:
                self.repository.fail_knowledge_sync_job(job_id=job_id, error_message="validation error")
            self.db.rollback()
            raise
        except SQLAlchemyError as exc:
            if job_id:
                self.repository.fail_knowledge_sync_job(job_id=job_id, error_message="database error during sync")
            self.db.rollback()
            raise ValueError("database error while syncing chatbot knowledge source") from exc

    def list_runtime_sources(
        self,
        *,
        hotel_id: str | None,
        source_group: str | None,
        is_active: bool | None,
    ) -> ChatbotRuntimeSourceListResponse:
        try:
            self.repository.ensure_schema()
            items = self.repository.list_runtime_sources(
                hotel_id=hotel_id,
                source_group=source_group,
                is_active=is_active,
            )
            self.db.commit()
            serialized = [self._serialize_runtime_source(item) for item in items]
            return ChatbotRuntimeSourceListResponse(items=serialized, total=len(serialized))
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while loading chatbot runtime sources") from exc

    def create_runtime_source(self, payload: ChatbotRuntimeSourceUpsertRequest) -> ChatbotRuntimeSourceResponse:
        try:
            self.repository.ensure_schema()
            item = self.repository.create_runtime_source(
                payload.model_dump(mode="json"),
                payload.updated_by_user_id,
            )
            self.db.commit()
            return self._serialize_runtime_source(item)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("runtime source already exists for this hotel, group, and code") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while creating chatbot runtime source") from exc

    def update_runtime_source(self, *, source_id: str, payload: ChatbotRuntimeSourceUpsertRequest) -> ChatbotRuntimeSourceResponse:
        try:
            self.repository.ensure_schema()
            item = self.repository.update_runtime_source(
                source_id=source_id,
                payload=payload.model_dump(mode="json"),
                updated_by_user_id=payload.updated_by_user_id,
            )
            if item is None:
                raise ValueError("runtime source not found")
            self.db.commit()
            return self._serialize_runtime_source(item)
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("runtime source already exists for this hotel, group, and code") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while updating chatbot runtime source") from exc

    def test_runtime_source(self, *, source_id: str) -> ChatbotRuntimeSourceTestResponse:
        try:
            self.repository.ensure_schema()
            item = self.repository.get_runtime_source(source_id=source_id)
            if item is None:
                raise ValueError("runtime source not found")

            if item["source_type"] in {"table", "view"}:
                target_ref = str(item["target_ref"])
                if not self.repository.can_select_from_target_ref(target_ref):
                    marked = self.repository.mark_runtime_source_test(
                        source_id=source_id,
                        status="error",
                        error_message="target_ref contains unsupported characters",
                    )
                    self.db.commit()
                    return ChatbotRuntimeSourceTestResponse(
                        id=source_id,
                        status="error",
                        checked_at=marked["last_checked_at"] if marked else datetime.now().astimezone(),
                        sample_result=None,
                        error_message="target_ref contains unsupported characters",
                    )

                sample_result = self.repository.select_target_sample(target_ref=target_ref)
                marked = self.repository.mark_runtime_source_test(source_id=source_id, status="ok", error_message=None)
                self.db.commit()
                return ChatbotRuntimeSourceTestResponse(
                    id=source_id,
                    status="ok",
                    checked_at=marked["last_checked_at"] if marked else datetime.now().astimezone(),
                    sample_result=sample_result,
                    error_message=None,
                )

            sample = {
                "message": "API source registered",
                "target_ref": item["target_ref"],
                "connection_name": item["connection_name"],
            }
            marked = self.repository.mark_runtime_source_test(source_id=source_id, status="ok", error_message=None)
            self.db.commit()
            return ChatbotRuntimeSourceTestResponse(
                id=source_id,
                status="ok",
                checked_at=marked["last_checked_at"] if marked else datetime.now().astimezone(),
                sample_result=sample,
                error_message=None,
            )
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ValueError("database error while testing chatbot runtime source") from exc

    def _serialize_hotel_settings(self, item: dict[str, object]) -> ChatbotHotelSettingsResponse:
        return ChatbotHotelSettingsResponse(
            hotel_id=str(item["hotel_id"]),
            hotel_name=str(item["hotel_name"]),
            hotel_code=str(item["hotel_code"]),
            bot_status=str(item["bot_status"]),
            default_language=str(item["default_language"]),
            supported_languages=list(item.get("supported_languages") or ["vi"]),
            confidence_threshold=float(item["confidence_threshold"]),
            handoff_threshold=float(item["handoff_threshold"]),
            allow_auto_reply=bool(item["allow_auto_reply"]),
            allow_after_hours_reply=bool(item["allow_after_hours_reply"]),
            allow_price_quote=bool(item["allow_price_quote"]),
            allow_inventory_lookup=bool(item["allow_inventory_lookup"]),
            allow_booking_status_lookup=bool(item["allow_booking_status_lookup"]),
            handoff_channel_code=str(item["handoff_channel_code"]) if item.get("handoff_channel_code") else None,
            handoff_target_ref=str(item["handoff_target_ref"]) if item.get("handoff_target_ref") else None,
            business_hours_json=dict(item.get("business_hours_json") or {}),
            notes=str(item["notes"]) if item.get("notes") else None,
            updated_by_user_id=str(item["updated_by_user_id"]) if item.get("updated_by_user_id") else None,
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
        )

    def _serialize_knowledge_source(self, item: dict[str, object]) -> ChatbotKnowledgeSourceResponse:
        return ChatbotKnowledgeSourceResponse(
            id=str(item["id"]),
            hotel_id=str(item["hotel_id"]),
            hotel_name=str(item["hotel_name"]),
            hotel_code=str(item["hotel_code"]),
            document_type=str(item["document_type"]),
            title=str(item["title"]),
            content=str(item["content"]),
            language=str(item["language"]),
            status=str(item["status"]),
            source_ref=str(item["source_ref"]),
            version=int(item["version"]),
            tags_json=list(item.get("tags_json") or []),
            metadata_json=dict(item.get("metadata_json") or {}),
            published_at=item.get("published_at"),
            published_by_user_id=str(item["published_by_user_id"]) if item.get("published_by_user_id") else None,
            synced_document_id=str(item["synced_document_id"]) if item.get("synced_document_id") else None,
            last_sync_job_id=str(item["last_sync_job_id"]) if item.get("last_sync_job_id") else None,
            last_sync_status=str(item["last_sync_status"]) if item.get("last_sync_status") else None,
            last_synced_at=item.get("last_synced_at"),
            chunk_count=int(item.get("chunk_count") or 0),
            updated_by_user_id=str(item["updated_by_user_id"]) if item.get("updated_by_user_id") else None,
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    def _serialize_runtime_source(self, item: dict[str, object]) -> ChatbotRuntimeSourceResponse:
        return ChatbotRuntimeSourceResponse(
            id=str(item["id"]),
            hotel_id=str(item["hotel_id"]),
            hotel_name=str(item["hotel_name"]),
            hotel_code=str(item["hotel_code"]),
            source_group=str(item["source_group"]),
            source_code=str(item["source_code"]),
            source_type=str(item["source_type"]),
            connection_name=str(item["connection_name"]),
            target_ref=str(item["target_ref"]),
            query_template=str(item["query_template"]) if item.get("query_template") else None,
            mapping_json=dict(item.get("mapping_json") or {}),
            is_active=bool(item["is_active"]),
            last_checked_at=item.get("last_checked_at"),
            last_status=str(item["last_status"]),
            last_error_message=str(item["last_error_message"]) if item.get("last_error_message") else None,
            updated_by_user_id=str(item["updated_by_user_id"]) if item.get("updated_by_user_id") else None,
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    def _chunk_text(self, content: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
        normalized = content.strip()
        if not normalized:
            return []
        if len(normalized) <= chunk_size:
            return [normalized]

        chunks: list[str] = []
        start = 0
        content_length = len(normalized)
        while start < content_length:
            end = min(start + chunk_size, content_length)
            if end < content_length:
                paragraph_break = normalized.rfind("\n\n", start, end)
                line_break = normalized.rfind("\n", start, end)
                sentence_break = max(
                    normalized.rfind(". ", start, end),
                    normalized.rfind("! ", start, end),
                    normalized.rfind("? ", start, end),
                )
                candidate = max(paragraph_break, line_break, sentence_break)
                if candidate > start + max(chunk_size // 3, 120):
                    end = candidate + (2 if candidate == sentence_break else 1)

            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= content_length:
                break
            start = max(end - chunk_overlap, start + 1)
        return chunks
