SET search_path TO public;

CREATE TABLE IF NOT EXISTS hotels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_code VARCHAR(50) NOT NULL UNIQUE,
    hotel_name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    timezone VARCHAR(100) NOT NULL DEFAULT 'Asia/Bangkok',
    country_code CHAR(2),
    city VARCHAR(120),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_hotels_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_code VARCHAR(50) NOT NULL UNIQUE,
    platform_name VARCHAR(120) NOT NULL,
    platform_type VARCHAR(50) NOT NULL DEFAULT 'review',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hotel_platform_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    external_account_id VARCHAR(255) NOT NULL,
    external_hotel_id VARCHAR(255),
    display_name VARCHAR(255),
    account_status VARCHAR(30) NOT NULL DEFAULT 'active',
    credentials_ref VARCHAR(255),
    sync_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,
    config JSONB NOT NULL DEFAULT '{}'::JSONB,
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hotel_platform_accounts UNIQUE (hotel_id, platform_id, external_account_id),
    CONSTRAINT chk_hotel_platform_accounts_status CHECK (account_status IN ('active', 'inactive', 'disconnected'))
);

CREATE TABLE IF NOT EXISTS hotel_platform_review_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    hotel_platform_account_id UUID REFERENCES hotel_platform_accounts(id) ON DELETE SET NULL,
    source_total_reviews INTEGER,
    source_average_rating NUMERIC(6,2),
    source_rating_scale NUMERIC(6,2),
    source_review_url TEXT,
    source_captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hotel_platform_review_metrics UNIQUE (hotel_id, platform_id),
    CONSTRAINT chk_hotel_platform_review_metrics_total_reviews CHECK (
        source_total_reviews IS NULL OR source_total_reviews >= 0
    ),
    CONSTRAINT chk_hotel_platform_review_metrics_average_rating CHECK (
        source_average_rating IS NULL OR source_average_rating >= 0
    ),
    CONSTRAINT chk_hotel_platform_review_metrics_rating_scale CHECK (
        source_rating_scale IS NULL OR source_rating_scale > 0
    )
);

CREATE TABLE IF NOT EXISTS room_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(120),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    occupancy_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_room_types_hotel_code UNIQUE (hotel_id, code),
    CONSTRAINT chk_room_types_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS rate_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    room_type_id UUID REFERENCES room_types(id) ON DELETE SET NULL,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    cancellation_policy JSONB NOT NULL DEFAULT '{}'::JSONB,
    meal_plan VARCHAR(100),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_rate_plans_hotel_code UNIQUE (hotel_id, code),
    CONSTRAINT chk_rate_plans_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    department_type VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_departments_hotel_code UNIQUE (hotel_id, code),
    CONSTRAINT chk_departments_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS review_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID REFERENCES hotels(id) ON DELETE CASCADE,
    tag_code VARCHAR(100) NOT NULL,
    tag_name VARCHAR(120) NOT NULL,
    tag_type VARCHAR(50) NOT NULL DEFAULT 'manual',
    color_hex VARCHAR(7),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_review_tags_scope UNIQUE (hotel_id, tag_code)
);

CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    hotel_platform_account_id UUID REFERENCES hotel_platform_accounts(id) ON DELETE SET NULL,
    external_review_id VARCHAR(255) NOT NULL,
    review_url TEXT,
    reviewer_name VARCHAR(255),
    reviewer_country_code CHAR(2),
    reviewer_profile JSONB NOT NULL DEFAULT '{}'::JSONB,
    rating NUMERIC(4,2),
    rating_scale NUMERIC(4,2),
    review_title TEXT,
    review_text TEXT,
    review_language VARCHAR(20),
    sentiment_label VARCHAR(30),
    is_bad_review BOOLEAN NOT NULL DEFAULT FALSE,
    stay_date DATE,
    reviewed_at TIMESTAMPTZ NOT NULL,
    replied_at TIMESTAMPTZ,
    source_created_at TIMESTAMPTZ,
    source_updated_at TIMESTAMPTZ,
    sync_version INTEGER NOT NULL DEFAULT 1,
    raw_payload JSONB NOT NULL,
    normalized_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reviews_dedup UNIQUE (hotel_id, platform_id, external_review_id),
    CONSTRAINT chk_reviews_sentiment CHECK (sentiment_label IS NULL OR sentiment_label IN ('positive', 'neutral', 'negative', 'mixed')),
    CONSTRAINT chk_reviews_rating CHECK (rating IS NULL OR rating >= 0),
    CONSTRAINT chk_reviews_rating_scale CHECK (rating_scale IS NULL OR rating_scale > 0)
);

CREATE TABLE IF NOT EXISTS review_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    external_reply_id VARCHAR(255),
    reply_text TEXT NOT NULL,
    replied_by VARCHAR(255),
    reply_language VARCHAR(20),
    source_created_at TIMESTAMPTZ,
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_review_replies_external UNIQUE (review_id, external_reply_id)
);

CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    analysis_type VARCHAR(100) NOT NULL,
    provider_name VARCHAR(100),
    model_name VARCHAR(120),
    model_version VARCHAR(120),
    sentiment_score NUMERIC(6,3),
    urgency_score NUMERIC(6,3),
    confidence_score NUMERIC(6,3),
    root_cause JSONB NOT NULL DEFAULT '[]'::JSONB,
    extracted_entities JSONB NOT NULL DEFAULT '[]'::JSONB,
    recommendations JSONB NOT NULL DEFAULT '[]'::JSONB,
    summary TEXT,
    result_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ai_analysis_version UNIQUE (review_id, analysis_type, model_version)
);

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    review_id UUID REFERENCES reviews(id) ON DELETE SET NULL,
    ai_analysis_result_id UUID REFERENCES ai_analysis_results(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    incident_type VARCHAR(100) NOT NULL,
    severity VARCHAR(30) NOT NULL DEFAULT 'medium',
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    occurred_at TIMESTAMPTZ,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    owner_name VARCHAR(255),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_incidents_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_incidents_status CHECK (status IN ('open', 'triaged', 'in_progress', 'resolved', 'ignored'))
);

CREATE TABLE IF NOT EXISTS sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    hotel_id UUID REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID REFERENCES platforms(id) ON DELETE RESTRICT,
    hotel_platform_account_id UUID REFERENCES hotel_platform_accounts(id) ON DELETE SET NULL,
    triggered_by VARCHAR(100) NOT NULL DEFAULT 'system',
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    request_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    response_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_message TEXT,
    records_fetched INTEGER NOT NULL DEFAULT 0,
    records_inserted INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_sync_jobs_status CHECK (status IN ('pending', 'running', 'success', 'partial_success', 'failed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    action VARCHAR(100) NOT NULL,
    actor_type VARCHAR(50) NOT NULL DEFAULT 'system',
    actor_id VARCHAR(255),
    hotel_id UUID REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID REFERENCES platforms(id) ON DELETE RESTRICT,
    before_data JSONB NOT NULL DEFAULT '{}'::JSONB,
    after_data JSONB NOT NULL DEFAULT '{}'::JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    channel_code VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL DEFAULT 'bad_review',
    delivery_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    target_ref VARCHAR(255),
    external_message_id VARCHAR(255),
    attempt_count INTEGER NOT NULL DEFAULT 1,
    first_attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    request_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    response_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_notification_deliveries UNIQUE (review_id, channel_code, event_type),
    CONSTRAINT chk_notification_deliveries_status CHECK (
        delivery_status IN ('pending', 'sent', 'failed', 'skipped')
    )
);
