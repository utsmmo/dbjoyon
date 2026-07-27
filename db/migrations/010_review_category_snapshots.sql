SET search_path TO public;

CREATE TABLE IF NOT EXISTS hotel_platform_category_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    hotel_platform_account_id UUID REFERENCES hotel_platform_accounts(id) ON DELETE SET NULL,
    source_captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    categories_payload JSONB NOT NULL DEFAULT '[]'::JSONB,
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_hotel_platform_category_snapshots UNIQUE (hotel_id, platform_id, source_captured_at)
);

CREATE INDEX IF NOT EXISTS idx_hotel_platform_category_snapshots_hotel_platform_captured
    ON hotel_platform_category_snapshots (hotel_id, platform_id, source_captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_hotel_platform_category_snapshots_platform_captured
    ON hotel_platform_category_snapshots (platform_id, source_captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_hotel_platform_category_snapshots_payload_gin
    ON hotel_platform_category_snapshots
    USING GIN (categories_payload);
