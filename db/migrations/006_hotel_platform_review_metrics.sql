SET search_path TO public;

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

CREATE INDEX IF NOT EXISTS idx_hotel_platform_review_metrics_hotel_platform
    ON hotel_platform_review_metrics (hotel_id, platform_id);

CREATE INDEX IF NOT EXISTS idx_hotel_platform_review_metrics_captured_at
    ON hotel_platform_review_metrics (source_captured_at DESC);
