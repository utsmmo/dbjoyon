SET search_path TO public;

COMMENT ON TABLE reviews IS
'Dedup strategy: unique key (hotel_id, platform_id, external_review_id). Upsert sync jobs should always target this key.';

COMMENT ON TABLE sync_jobs IS
'Integration log for n8n, cron, or internal sync workers. PostgreSQL remains the single source of truth.';

COMMENT ON COLUMN reviews.raw_payload IS
'Full original review payload from OTA/platform API for traceability and schema drift tolerance.';

COMMENT ON COLUMN ai_analysis_results.result_payload IS
'Full AI output payload for auditability and model iteration.';

/*
Example review upsert for future API or worker:

INSERT INTO reviews (
    hotel_id,
    platform_id,
    hotel_platform_account_id,
    external_review_id,
    review_url,
    reviewer_name,
    rating,
    rating_scale,
    review_title,
    review_text,
    review_language,
    sentiment_label,
    is_bad_review,
    stay_date,
    reviewed_at,
    source_created_at,
    source_updated_at,
    raw_payload,
    normalized_payload,
    metadata
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    NULL,
    'booking-review-987654',
    'https://example.com/review/987654',
    'John Doe',
    4.00,
    10.00,
    'Nice stay',
    'The room was clean but breakfast was slow.',
    'en',
    'mixed',
    FALSE,
    '2026-07-15',
    '2026-07-16T10:15:00+07:00',
    '2026-07-16T10:15:00+07:00',
    '2026-07-16T10:30:00+07:00',
    '{"provider":"booking","review_id":"booking-review-987654"}'::JSONB,
    '{"topics":["cleanliness","breakfast"]}'::JSONB,
    '{"sync_source":"manual_example"}'::JSONB
)
ON CONFLICT (hotel_id, platform_id, external_review_id)
DO UPDATE SET
    hotel_platform_account_id = EXCLUDED.hotel_platform_account_id,
    review_url = EXCLUDED.review_url,
    reviewer_name = EXCLUDED.reviewer_name,
    rating = EXCLUDED.rating,
    rating_scale = EXCLUDED.rating_scale,
    review_title = EXCLUDED.review_title,
    review_text = EXCLUDED.review_text,
    review_language = EXCLUDED.review_language,
    sentiment_label = EXCLUDED.sentiment_label,
    is_bad_review = EXCLUDED.is_bad_review,
    stay_date = EXCLUDED.stay_date,
    reviewed_at = EXCLUDED.reviewed_at,
    source_created_at = EXCLUDED.source_created_at,
    source_updated_at = EXCLUDED.source_updated_at,
    raw_payload = EXCLUDED.raw_payload,
    normalized_payload = EXCLUDED.normalized_payload,
    metadata = EXCLUDED.metadata,
    sync_version = reviews.sync_version + 1,
    updated_at = NOW();
*/
