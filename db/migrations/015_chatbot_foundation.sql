SET search_path TO public;

CREATE TABLE IF NOT EXISTS chatbot_hotel_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL,
    channel_name VARCHAR(120) NOT NULL,
    external_channel_key VARCHAR(255) NOT NULL,
    language_hint VARCHAR(20),
    brand_tone_override TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chatbot_hotel_channels_external_key UNIQUE (external_channel_key),
    CONSTRAINT chk_chatbot_hotel_channels_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS chatbot_guests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_guest_key VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chatbot_guests_external_guest_key UNIQUE (external_guest_key)
);

CREATE TABLE IF NOT EXISTS chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES chatbot_hotel_channels(id) ON DELETE CASCADE,
    guest_id UUID REFERENCES chatbot_guests(id) ON DELETE SET NULL,
    external_conversation_id VARCHAR(255) NOT NULL,
    booking_id VARCHAR(255),
    detected_language VARCHAR(20),
    current_intent VARCHAR(120),
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    assigned_staff_id UUID REFERENCES users(id) ON DELETE SET NULL,
    staff_assigned_at TIMESTAMPTZ,
    last_message_at TIMESTAMPTZ,
    last_bot_confidence NUMERIC(6,3),
    last_risk_level VARCHAR(20),
    short_memory_summary TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chatbot_conversations_channel_external UNIQUE (channel_id, external_conversation_id),
    CONSTRAINT chk_chatbot_conversations_status CHECK (status IN ('open', 'pending_handoff', 'resolved', 'closed')),
    CONSTRAINT chk_chatbot_conversations_last_risk_level CHECK (
        last_risk_level IS NULL OR last_risk_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT chk_chatbot_conversations_last_bot_confidence CHECK (
        last_bot_confidence IS NULL OR (last_bot_confidence >= 0 AND last_bot_confidence <= 1)
    )
);

CREATE TABLE IF NOT EXISTS chatbot_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chatbot_conversations(id) ON DELETE CASCADE,
    external_message_id VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    translated_content TEXT,
    detected_language VARCHAR(20),
    intent VARCHAR(120),
    confidence_score NUMERIC(6,3),
    risk_level VARCHAR(20),
    handoff_flag BOOLEAN NOT NULL DEFAULT FALSE,
    handoff_reason TEXT,
    sources_used JSONB NOT NULL DEFAULT '[]'::JSONB,
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chatbot_messages_external_message_id UNIQUE (external_message_id),
    CONSTRAINT chk_chatbot_messages_role CHECK (role IN ('guest', 'bot', 'staff', 'system')),
    CONSTRAINT chk_chatbot_messages_risk_level CHECK (
        risk_level IS NULL OR risk_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT chk_chatbot_messages_confidence_score CHECK (
        confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)
    )
);

CREATE TABLE IF NOT EXISTS chatbot_knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    document_type VARCHAR(80) NOT NULL,
    title VARCHAR(255) NOT NULL,
    language VARCHAR(20) NOT NULL DEFAULT 'vi',
    source VARCHAR(80) NOT NULL,
    source_ref VARCHAR(255) NOT NULL,
    content_raw TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chatbot_knowledge_documents_version UNIQUE (hotel_id, document_type, source_ref, version)
);

CREATE TABLE IF NOT EXISTS chatbot_knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES chatbot_knowledge_documents(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    language VARCHAR(20) NOT NULL DEFAULT 'vi',
    chunk_order INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    vector_ref VARCHAR(255),
    keywords JSONB NOT NULL DEFAULT '[]'::JSONB,
    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chatbot_knowledge_chunks_order UNIQUE (document_id, chunk_order)
);

CREATE TABLE IF NOT EXISTS chatbot_guest_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id UUID NOT NULL REFERENCES chatbot_guests(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    language_preference VARCHAR(20),
    special_preferences TEXT,
    important_notes TEXT,
    last_stay_info JSONB NOT NULL DEFAULT '{}'::JSONB,
    memory_version INTEGER NOT NULL DEFAULT 1,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chatbot_guest_memory_guest_hotel UNIQUE (guest_id, hotel_id)
);

CREATE TABLE IF NOT EXISTS chatbot_handoff_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chatbot_conversations(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES chatbot_messages(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    confidence_score NUMERIC(6,3),
    risk_level VARCHAR(20) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    status VARCHAR(30) NOT NULL DEFAULT 'queued',
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_chatbot_handoff_queue_risk_level CHECK (risk_level IN ('low', 'medium', 'high')),
    CONSTRAINT chk_chatbot_handoff_queue_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    CONSTRAINT chk_chatbot_handoff_queue_status CHECK (
        status IN ('queued', 'sent_to_lark', 'acknowledged', 'resolved', 'cancelled')
    ),
    CONSTRAINT chk_chatbot_handoff_queue_confidence_score CHECK (
        confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)
    )
);

CREATE TABLE IF NOT EXISTS chatbot_feedback_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES chatbot_conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES chatbot_messages(id) ON DELETE CASCADE,
    bot_answer TEXT,
    staff_corrected_answer TEXT,
    outcome VARCHAR(20) NOT NULL,
    improvement_type VARCHAR(30),
    root_cause TEXT,
    notes TEXT,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_chatbot_feedback_learning_outcome CHECK (outcome IN ('correct', 'partial', 'wrong')),
    CONSTRAINT chk_chatbot_feedback_learning_improvement_type CHECK (
        improvement_type IS NULL OR improvement_type IN ('knowledge', 'prompt', 'routing', 'policy', 'runtime_data')
    )
);

CREATE TABLE IF NOT EXISTS chatbot_knowledge_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(80) NOT NULL,
    source_ref VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    input_ref VARCHAR(255),
    output_ref VARCHAR(255),
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_chatbot_knowledge_sync_jobs_status CHECK (
        status IN ('pending', 'running', 'done', 'failed', 'cancelled')
    )
);

CREATE INDEX IF NOT EXISTS idx_chatbot_hotel_channels_hotel_type_status
    ON chatbot_hotel_channels (hotel_id, channel_type, status);

CREATE INDEX IF NOT EXISTS idx_chatbot_guests_display_name
    ON chatbot_guests (display_name);

CREATE INDEX IF NOT EXISTS idx_chatbot_guests_phone
    ON chatbot_guests (phone);

CREATE INDEX IF NOT EXISTS idx_chatbot_guests_email
    ON chatbot_guests (email);

CREATE INDEX IF NOT EXISTS idx_chatbot_conversations_hotel_status_last_message
    ON chatbot_conversations (hotel_id, status, last_message_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_messages_conversation_created_at
    ON chatbot_messages (conversation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_chatbot_messages_handoff_risk_created_at
    ON chatbot_messages (handoff_flag, risk_level, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_knowledge_documents_hotel_type_active
    ON chatbot_knowledge_documents (hotel_id, document_type, is_active);

CREATE INDEX IF NOT EXISTS idx_chatbot_knowledge_chunks_hotel_language
    ON chatbot_knowledge_chunks (hotel_id, language);

CREATE INDEX IF NOT EXISTS idx_chatbot_guest_memory_hotel_updated_at
    ON chatbot_guest_memory (hotel_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_handoff_queue_hotel_status_priority_created
    ON chatbot_handoff_queue (hotel_id, status, priority, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_handoff_queue_assigned_status_created
    ON chatbot_handoff_queue (assigned_to, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_feedback_learning_hotel_outcome_created
    ON chatbot_feedback_learning (hotel_id, outcome, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_knowledge_sync_jobs_hotel_job_status_created
    ON chatbot_knowledge_sync_jobs (hotel_id, job_type, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chatbot_knowledge_sync_jobs_source_created
    ON chatbot_knowledge_sync_jobs (source_name, source_ref, created_at DESC);
