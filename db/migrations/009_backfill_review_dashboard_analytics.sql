SET search_path TO public;

BEGIN;

TRUNCATE TABLE
    review_dashboard_current_metrics,
    review_dashboard_daily_metrics,
    review_dashboard_daily_country_metrics,
    review_dashboard_daily_score_buckets;

WITH source_metrics AS (
    SELECT
        m.hotel_id,
        m.platform_id,
        m.source_total_reviews,
        m.source_average_rating,
        m.source_rating_scale
    FROM hotel_platform_review_metrics m
),
daily_base AS (
    SELECT
        DATE(r.reviewed_at AT TIME ZONE 'Asia/Bangkok') AS metric_date,
        r.hotel_id,
        r.platform_id,
        COUNT(*)::int AS total_reviews,
        COUNT(*) FILTER (WHERE r.is_bad_review = TRUE)::int AS bad_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'positive')::int AS positive_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'neutral')::int AS neutral_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'negative')::int AS negative_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'mixed')::int AS mixed_reviews,
        AVG(r.rating)::numeric(8,4) AS avg_rating,
        MIN(r.rating)::numeric(6,2) AS min_rating,
        MAX(r.rating)::numeric(6,2) AS max_rating,
        MAX(r.reviewed_at) AS latest_reviewed_at,
        MAX(r.source_updated_at) AS latest_source_updated_at
    FROM reviews r
    GROUP BY
        DATE(r.reviewed_at AT TIME ZONE 'Asia/Bangkok'),
        r.hotel_id,
        r.platform_id
)
INSERT INTO review_dashboard_daily_metrics (
    metric_date,
    hotel_id,
    platform_id,
    total_reviews,
    bad_reviews,
    positive_reviews,
    neutral_reviews,
    negative_reviews,
    mixed_reviews,
    avg_rating,
    min_rating,
    max_rating,
    latest_reviewed_at,
    latest_source_updated_at,
    source_total_reviews,
    source_average_rating,
    source_rating_scale,
    metadata
)
SELECT
    d.metric_date,
    d.hotel_id,
    d.platform_id,
    d.total_reviews,
    d.bad_reviews,
    d.positive_reviews,
    d.neutral_reviews,
    d.negative_reviews,
    d.mixed_reviews,
    d.avg_rating,
    d.min_rating,
    d.max_rating,
    d.latest_reviewed_at,
    d.latest_source_updated_at,
    sm.source_total_reviews,
    sm.source_average_rating,
    sm.source_rating_scale,
    jsonb_build_object('backfill', true)
FROM daily_base d
LEFT JOIN source_metrics sm
    ON sm.hotel_id = d.hotel_id
   AND sm.platform_id = d.platform_id;

WITH source_metrics AS (
    SELECT
        m.hotel_id,
        m.platform_id,
        m.source_total_reviews,
        m.source_average_rating,
        m.source_rating_scale
    FROM hotel_platform_review_metrics m
),
current_base AS (
    SELECT
        r.hotel_id,
        r.platform_id,
        COUNT(*)::int AS total_reviews,
        COUNT(*) FILTER (WHERE r.is_bad_review = TRUE)::int AS bad_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'positive')::int AS positive_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'neutral')::int AS neutral_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'negative')::int AS negative_reviews,
        COUNT(*) FILTER (WHERE r.sentiment_label = 'mixed')::int AS mixed_reviews,
        AVG(r.rating)::numeric(8,4) AS avg_rating,
        MIN(r.rating)::numeric(6,2) AS min_rating,
        MAX(r.rating)::numeric(6,2) AS max_rating,
        MAX(r.reviewed_at) AS latest_reviewed_at,
        MAX(r.source_updated_at) AS latest_source_updated_at
    FROM reviews r
    GROUP BY
        r.hotel_id,
        r.platform_id
)
INSERT INTO review_dashboard_current_metrics (
    hotel_id,
    platform_id,
    total_reviews,
    bad_reviews,
    positive_reviews,
    neutral_reviews,
    negative_reviews,
    mixed_reviews,
    avg_rating,
    min_rating,
    max_rating,
    latest_reviewed_at,
    latest_source_updated_at,
    source_total_reviews,
    source_average_rating,
    source_rating_scale,
    last_aggregated_at,
    metadata
)
SELECT
    c.hotel_id,
    c.platform_id,
    c.total_reviews,
    c.bad_reviews,
    c.positive_reviews,
    c.neutral_reviews,
    c.negative_reviews,
    c.mixed_reviews,
    c.avg_rating,
    c.min_rating,
    c.max_rating,
    c.latest_reviewed_at,
    c.latest_source_updated_at,
    sm.source_total_reviews,
    sm.source_average_rating,
    sm.source_rating_scale,
    NOW(),
    jsonb_build_object('backfill', true)
FROM current_base c
LEFT JOIN source_metrics sm
    ON sm.hotel_id = c.hotel_id
   AND sm.platform_id = c.platform_id;

INSERT INTO review_dashboard_daily_country_metrics (
    metric_date,
    hotel_id,
    platform_id,
    reviewer_country_code,
    total_reviews,
    bad_reviews,
    avg_rating
)
SELECT
    DATE(r.reviewed_at AT TIME ZONE 'Asia/Bangkok') AS metric_date,
    r.hotel_id,
    r.platform_id,
    UPPER(r.reviewer_country_code) AS reviewer_country_code,
    COUNT(*)::int AS total_reviews,
    COUNT(*) FILTER (WHERE r.is_bad_review = TRUE)::int AS bad_reviews,
    AVG(r.rating)::numeric(8,4) AS avg_rating
FROM reviews r
WHERE COALESCE(TRIM(r.reviewer_country_code), '') <> ''
GROUP BY
    DATE(r.reviewed_at AT TIME ZONE 'Asia/Bangkok'),
    r.hotel_id,
    r.platform_id,
    UPPER(r.reviewer_country_code);

WITH normalized_reviews AS (
    SELECT
        DATE(r.reviewed_at AT TIME ZONE 'Asia/Bangkok') AS metric_date,
        r.hotel_id,
        r.platform_id,
        r.is_bad_review,
        CASE
            WHEN r.rating IS NULL OR r.rating_scale IS NULL OR r.rating_scale = 0 THEN NULL
            WHEN r.rating_scale = 10 THEN r.rating::numeric
            ELSE ROUND((r.rating * 10.0 / r.rating_scale)::numeric, 2)
        END AS normalized_rating
    FROM reviews r
),
bucketed AS (
    SELECT
        n.metric_date,
        n.hotel_id,
        n.platform_id,
        n.is_bad_review,
        n.normalized_rating,
        CASE
            WHEN n.normalized_rating IS NULL THEN 'unrated'
            WHEN n.normalized_rating < 2 THEN '0_2'
            WHEN n.normalized_rating < 4 THEN '2_4'
            WHEN n.normalized_rating < 6 THEN '4_6'
            WHEN n.normalized_rating < 8 THEN '6_8'
            WHEN n.normalized_rating < 9 THEN '8_9'
            ELSE '9_10'
        END AS bucket_code,
        CASE
            WHEN n.normalized_rating IS NULL THEN 'Unrated'
            WHEN n.normalized_rating < 2 THEN '0.0 - 1.99'
            WHEN n.normalized_rating < 4 THEN '2.0 - 3.99'
            WHEN n.normalized_rating < 6 THEN '4.0 - 5.99'
            WHEN n.normalized_rating < 8 THEN '6.0 - 7.99'
            WHEN n.normalized_rating < 9 THEN '8.0 - 8.99'
            ELSE '9.0 - 10.0'
        END AS bucket_label,
        CASE
            WHEN n.normalized_rating IS NULL THEN 0.0
            WHEN n.normalized_rating < 2 THEN 0.0
            WHEN n.normalized_rating < 4 THEN 2.0
            WHEN n.normalized_rating < 6 THEN 4.0
            WHEN n.normalized_rating < 8 THEN 6.0
            WHEN n.normalized_rating < 9 THEN 8.0
            ELSE 9.0
        END AS rating_from,
        CASE
            WHEN n.normalized_rating IS NULL THEN 0.0
            WHEN n.normalized_rating < 2 THEN 1.99
            WHEN n.normalized_rating < 4 THEN 3.99
            WHEN n.normalized_rating < 6 THEN 5.99
            WHEN n.normalized_rating < 8 THEN 7.99
            WHEN n.normalized_rating < 9 THEN 8.99
            ELSE 10.0
        END AS rating_to
    FROM normalized_reviews n
)
INSERT INTO review_dashboard_daily_score_buckets (
    metric_date,
    hotel_id,
    platform_id,
    bucket_code,
    bucket_label,
    rating_from,
    rating_to,
    review_count,
    bad_review_count
)
SELECT
    b.metric_date,
    b.hotel_id,
    b.platform_id,
    b.bucket_code,
    MIN(b.bucket_label) AS bucket_label,
    MIN(b.rating_from)::numeric(6,2) AS rating_from,
    MAX(b.rating_to)::numeric(6,2) AS rating_to,
    COUNT(*)::int AS review_count,
    COUNT(*) FILTER (WHERE b.is_bad_review = TRUE)::int AS bad_review_count
FROM bucketed b
GROUP BY
    b.metric_date,
    b.hotel_id,
    b.platform_id,
    b.bucket_code;

COMMIT;
