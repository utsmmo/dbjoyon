BEGIN;

WITH normalized_reviews AS (
    SELECT
        r.id,
        CASE
            WHEN r.rating IS NULL OR r.rating_scale IS NULL OR r.rating_scale = 0 THEN NULL
            WHEN r.rating_scale = 10 THEN r.rating::numeric
            ELSE ROUND((r.rating * 10.0 / r.rating_scale)::numeric, 2)
        END AS normalized_rating
    FROM reviews r
)
UPDATE reviews r
SET
    is_bad_review = CASE
        WHEN n.normalized_rating IS NULL THEN COALESCE(r.is_bad_review, FALSE)
        WHEN n.normalized_rating < 7 THEN TRUE
        ELSE FALSE
    END
FROM normalized_reviews n
WHERE r.id = n.id;

COMMIT;
