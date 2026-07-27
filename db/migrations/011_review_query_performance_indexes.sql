SET search_path TO public;

CREATE INDEX IF NOT EXISTS idx_reviews_platform_reviewed_at_desc
    ON reviews (platform_id, reviewed_at DESC);

CREATE INDEX IF NOT EXISTS idx_reviews_platform_rating_reviewed_at_desc
    ON reviews (platform_id, rating DESC, reviewed_at DESC)
    WHERE rating IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_country_reviewed_at_desc
    ON reviews (reviewer_country_code, reviewed_at DESC)
    WHERE reviewer_country_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reviews_platform_bad_reviewed_at_desc
    ON reviews (platform_id, is_bad_review, reviewed_at DESC);
