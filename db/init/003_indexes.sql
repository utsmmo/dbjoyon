SET search_path TO public;

CREATE INDEX IF NOT EXISTS idx_hotel_platform_accounts_hotel_id
    ON hotel_platform_accounts (hotel_id);

CREATE INDEX IF NOT EXISTS idx_hotel_platform_accounts_platform_id
    ON hotel_platform_accounts (platform_id);

CREATE INDEX IF NOT EXISTS idx_hotel_platform_review_metrics_hotel_platform
    ON hotel_platform_review_metrics (hotel_id, platform_id);

CREATE INDEX IF NOT EXISTS idx_hotel_platform_review_metrics_captured_at
    ON hotel_platform_review_metrics (source_captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_room_types_hotel_id
    ON room_types (hotel_id);

CREATE INDEX IF NOT EXISTS idx_rate_plans_hotel_id
    ON rate_plans (hotel_id);

CREATE INDEX IF NOT EXISTS idx_rate_plans_room_type_id
    ON rate_plans (room_type_id);

CREATE INDEX IF NOT EXISTS idx_departments_hotel_id
    ON departments (hotel_id);

CREATE INDEX IF NOT EXISTS idx_reviews_hotel_id
    ON reviews (hotel_id);

CREATE INDEX IF NOT EXISTS idx_reviews_platform_id
    ON reviews (platform_id);

CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at
    ON reviews (reviewed_at DESC);

CREATE INDEX IF NOT EXISTS idx_reviews_hotel_platform_reviewed_at
    ON reviews (hotel_id, platform_id, reviewed_at DESC);

CREATE INDEX IF NOT EXISTS idx_reviews_bad_review
    ON reviews (hotel_id, is_bad_review, reviewed_at DESC);

CREATE INDEX IF NOT EXISTS idx_reviews_external_lookup
    ON reviews (platform_id, external_review_id);

CREATE INDEX IF NOT EXISTS idx_reviews_raw_payload_gin
    ON reviews
    USING GIN (raw_payload);

CREATE INDEX IF NOT EXISTS idx_reviews_normalized_payload_gin
    ON reviews
    USING GIN (normalized_payload);

CREATE INDEX IF NOT EXISTS idx_review_replies_review_id
    ON review_replies (review_id);

CREATE INDEX IF NOT EXISTS idx_ai_analysis_review_id
    ON ai_analysis_results (review_id);

CREATE INDEX IF NOT EXISTS idx_ai_analysis_lookup
    ON ai_analysis_results (hotel_id, analysis_type, analyzed_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_analysis_result_payload_gin
    ON ai_analysis_results
    USING GIN (result_payload);

CREATE INDEX IF NOT EXISTS idx_incidents_hotel_status
    ON incidents (hotel_id, status, severity, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_incidents_review_id
    ON incidents (review_id);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_status_created_at
    ON sync_jobs (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_hotel_platform
    ON sync_jobs (hotel_id, platform_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
    ON audit_logs (entity_type, entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_hotel_created_at
    ON audit_logs (hotel_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notification_deliveries_channel_status
    ON notification_deliveries (channel_code, delivery_status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notification_deliveries_review_id
    ON notification_deliveries (review_id);

CREATE INDEX IF NOT EXISTS idx_notification_deliveries_hotel_channel
    ON notification_deliveries (hotel_id, channel_code, delivery_status, created_at DESC);
