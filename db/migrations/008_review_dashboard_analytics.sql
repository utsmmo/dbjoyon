SET search_path TO public;

-- Aggregate table cho dashboard theo ngày / hotel / platform.
-- Dashboard summary và hotel breakdown nên đọc chủ yếu từ bảng này.
CREATE TABLE IF NOT EXISTS review_dashboard_daily_metrics (
    metric_date DATE NOT NULL,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    bad_reviews INTEGER NOT NULL DEFAULT 0,
    positive_reviews INTEGER NOT NULL DEFAULT 0,
    neutral_reviews INTEGER NOT NULL DEFAULT 0,
    negative_reviews INTEGER NOT NULL DEFAULT 0,
    mixed_reviews INTEGER NOT NULL DEFAULT 0,
    avg_rating NUMERIC(8,4),
    min_rating NUMERIC(6,2),
    max_rating NUMERIC(6,2),
    latest_reviewed_at TIMESTAMPTZ,
    latest_source_updated_at TIMESTAMPTZ,
    source_total_reviews INTEGER,
    source_average_rating NUMERIC(6,2),
    source_rating_scale NUMERIC(6,2),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (metric_date, hotel_id, platform_id)
);

-- Aggregate theo ngày / hotel / platform / reviewer country.
-- Endpoint country breakdown đọc từ đây thay vì group trực tiếp từ reviews.
CREATE TABLE IF NOT EXISTS review_dashboard_daily_country_metrics (
    metric_date DATE NOT NULL,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    reviewer_country_code CHAR(2) NOT NULL,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    bad_reviews INTEGER NOT NULL DEFAULT 0,
    avg_rating NUMERIC(8,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (metric_date, hotel_id, platform_id, reviewer_country_code)
);

-- Aggregate theo ngày / hotel / platform / bucket điểm.
-- Endpoint score buckets đọc từ đây.
CREATE TABLE IF NOT EXISTS review_dashboard_daily_score_buckets (
    metric_date DATE NOT NULL,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    bucket_code VARCHAR(30) NOT NULL,
    bucket_label VARCHAR(50) NOT NULL,
    rating_from NUMERIC(6,2) NOT NULL,
    rating_to NUMERIC(6,2) NOT NULL,
    review_count INTEGER NOT NULL DEFAULT 0,
    bad_review_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (metric_date, hotel_id, platform_id, bucket_code)
);

-- Snapshot current để summary card load rất nhanh.
-- Mỗi hotel/platform có đúng 1 dòng current.
CREATE TABLE IF NOT EXISTS review_dashboard_current_metrics (
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    bad_reviews INTEGER NOT NULL DEFAULT 0,
    positive_reviews INTEGER NOT NULL DEFAULT 0,
    neutral_reviews INTEGER NOT NULL DEFAULT 0,
    negative_reviews INTEGER NOT NULL DEFAULT 0,
    mixed_reviews INTEGER NOT NULL DEFAULT 0,
    avg_rating NUMERIC(8,4),
    min_rating NUMERIC(6,2),
    max_rating NUMERIC(6,2),
    latest_reviewed_at TIMESTAMPTZ,
    latest_source_updated_at TIMESTAMPTZ,
    source_total_reviews INTEGER,
    source_average_rating NUMERIC(6,2),
    source_rating_scale NUMERIC(6,2),
    last_aggregated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (hotel_id, platform_id)
);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_daily_metrics_hotel_date
    ON review_dashboard_daily_metrics (hotel_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_daily_metrics_platform_date
    ON review_dashboard_daily_metrics (platform_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_daily_metrics_date
    ON review_dashboard_daily_metrics (metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_daily_country_metrics_lookup
    ON review_dashboard_daily_country_metrics (hotel_id, platform_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_daily_country_metrics_country
    ON review_dashboard_daily_country_metrics (reviewer_country_code, metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_daily_score_buckets_lookup
    ON review_dashboard_daily_score_buckets (hotel_id, platform_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_current_metrics_hotel
    ON review_dashboard_current_metrics (hotel_id);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_current_metrics_platform
    ON review_dashboard_current_metrics (platform_id);

CREATE INDEX IF NOT EXISTS idx_review_dashboard_current_metrics_latest
    ON review_dashboard_current_metrics (last_aggregated_at DESC);
