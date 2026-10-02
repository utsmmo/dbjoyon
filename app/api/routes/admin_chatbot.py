from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_session
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
from app.services.admin_chatbot_service import AdminChatbotService

router = APIRouter(prefix="/admin/chatbot", tags=["admin-chatbot"])


@router.get("/hotels", response_model=ChatbotHotelSettingsListResponse)
def list_hotel_bot_settings(db: Session = Depends(db_session)) -> ChatbotHotelSettingsListResponse:
    service = AdminChatbotService(db)
    try:
        return service.list_hotel_settings()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/hotels/{hotel_id}/settings", response_model=ChatbotHotelSettingsResponse)
def get_hotel_bot_settings(hotel_id: str, db: Session = Depends(db_session)) -> ChatbotHotelSettingsResponse:
    service = AdminChatbotService(db)
    try:
        return service.get_hotel_settings(hotel_id=hotel_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.put("/hotels/{hotel_id}/settings", response_model=ChatbotHotelSettingsResponse)
def update_hotel_bot_settings(
    hotel_id: str,
    payload: ChatbotHotelSettingsUpdateRequest,
    db: Session = Depends(db_session),
) -> ChatbotHotelSettingsResponse:
    service = AdminChatbotService(db)
    try:
        return service.update_hotel_settings(hotel_id=hotel_id, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/knowledge-sources", response_model=ChatbotKnowledgeSourceListResponse)
def list_knowledge_sources(
    hotel_id: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    language: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_session),
) -> ChatbotKnowledgeSourceListResponse:
    service = AdminChatbotService(db)
    try:
        return service.list_knowledge_sources(
            hotel_id=hotel_id,
            document_type=document_type,
            status=status_filter,
            language=language,
            q=q,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/knowledge-sources", response_model=ChatbotKnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_source(
    payload: ChatbotKnowledgeSourceUpsertRequest,
    db: Session = Depends(db_session),
) -> ChatbotKnowledgeSourceResponse:
    service = AdminChatbotService(db)
    try:
        return service.create_knowledge_source(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/knowledge-sources/{source_id}", response_model=ChatbotKnowledgeSourceResponse)
def update_knowledge_source(
    source_id: str,
    payload: ChatbotKnowledgeSourceUpsertRequest,
    db: Session = Depends(db_session),
) -> ChatbotKnowledgeSourceResponse:
    service = AdminChatbotService(db)
    try:
        return service.update_knowledge_source(source_id=source_id, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/knowledge-sources/{source_id}/publish", response_model=ChatbotKnowledgeSourceResponse)
def publish_knowledge_source(
    source_id: str,
    payload: ChatbotKnowledgePublishRequest,
    db: Session = Depends(db_session),
) -> ChatbotKnowledgeSourceResponse:
    service = AdminChatbotService(db)
    try:
        return service.publish_knowledge_source(source_id=source_id, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/knowledge-sources/{source_id}/sync", response_model=ChatbotKnowledgeSyncResponse)
def sync_knowledge_source(
    source_id: str,
    payload: ChatbotKnowledgeSyncRequest,
    db: Session = Depends(db_session),
) -> ChatbotKnowledgeSyncResponse:
    service = AdminChatbotService(db)
    try:
        return service.sync_knowledge_source(source_id=source_id, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/runtime-sources", response_model=ChatbotRuntimeSourceListResponse)
def list_runtime_sources(
    hotel_id: str | None = Query(default=None),
    source_group: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(db_session),
) -> ChatbotRuntimeSourceListResponse:
    service = AdminChatbotService(db)
    try:
        return service.list_runtime_sources(
            hotel_id=hotel_id,
            source_group=source_group,
            is_active=is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runtime-sources", response_model=ChatbotRuntimeSourceResponse, status_code=status.HTTP_201_CREATED)
def create_runtime_source(
    payload: ChatbotRuntimeSourceUpsertRequest,
    db: Session = Depends(db_session),
) -> ChatbotRuntimeSourceResponse:
    service = AdminChatbotService(db)
    try:
        return service.create_runtime_source(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/runtime-sources/{source_id}", response_model=ChatbotRuntimeSourceResponse)
def update_runtime_source(
    source_id: str,
    payload: ChatbotRuntimeSourceUpsertRequest,
    db: Session = Depends(db_session),
) -> ChatbotRuntimeSourceResponse:
    service = AdminChatbotService(db)
    try:
        return service.update_runtime_source(source_id=source_id, payload=payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/runtime-sources/{source_id}/test", response_model=ChatbotRuntimeSourceTestResponse)
def test_runtime_source(source_id: str, db: Session = Depends(db_session)) -> ChatbotRuntimeSourceTestResponse:
    service = AdminChatbotService(db)
    try:
        return service.test_runtime_source(source_id=source_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
