-- AIRBNB_GOOGLE_DB_REPAIR.sql
-- Muc tieu:
-- 1. Rà toàn bo hotel co link Airbnb bi luu nham trong source_links.google
-- 2. Rà toàn bo hotel co link Google bi luu nham trong source_links.airbnb
-- 3. Sua metadata va hotel_platform_accounts de backend sync dung platform
--
-- Luu y:
-- - File nay la playbook van hanh, khong phai migration auto chay.
-- - Chay tung block, verify xong moi COMMIT.

-- ============================================================
-- A. Detect hotel dang co link Airbnb nam nham trong Google
-- ============================================================

SELECT
    h.id,
    h.hotel_code,
    h.hotel_name,
    value::text AS misplaced_link
FROM hotels h,
LATERAL jsonb_array_elements(COALESCE(h.metadata->'source_links'->'google', '[]'::jsonb)) AS value
WHERE value::text ILIKE '%airbnb%';

-- ============================================================
-- B. Detect hotel dang co link Google nam nham trong Airbnb
-- ============================================================

SELECT
    h.id,
    h.hotel_code,
    h.hotel_name,
    value::text AS misplaced_link
FROM hotels h,
LATERAL jsonb_array_elements(COALESCE(h.metadata->'source_links'->'airbnb', '[]'::jsonb)) AS value
WHERE value::text ILIKE '%google%'
   OR value::text ILIKE '%maps%';

-- ============================================================
-- C. Detect hotel_platform_accounts dang map sai platform
-- ============================================================

SELECT
    hpa.id,
    h.hotel_code,
    h.hotel_name,
    p.platform_code,
    hpa.external_account_id
FROM hotel_platform_accounts hpa
JOIN hotels h ON h.id = hpa.hotel_id
JOIN platforms p ON p.id = hpa.platform_id
WHERE (p.platform_code = 'google' AND hpa.external_account_id ILIKE '%airbnb%')
   OR (p.platform_code = 'airbnb' AND (
        hpa.external_account_id ILIKE '%google%'
        OR hpa.external_account_id ILIKE '%maps%'
   ));

-- ============================================================
-- D. Fix 1 hotel cu the
-- Thay:
--   :hotel_id
--   :misplaced_link
--   :google_place_id
--   :airbnb_room_id
-- truoc khi chay
-- ============================================================

BEGIN;

WITH source_row AS (
    SELECT
        h.id,
        h.metadata
    FROM hotels h
    WHERE h.id = CAST(:hotel_id AS uuid)
),
updated_hotel AS (
    UPDATE hotels h
    SET metadata = jsonb_set(
        jsonb_set(
            jsonb_set(
                jsonb_set(
                    COALESCE(h.metadata, '{}'::jsonb),
                    '{source_links,google}',
                    COALESCE(
                        (
                            SELECT jsonb_agg(value)
                            FROM jsonb_array_elements(COALESCE(h.metadata->'source_links'->'google', '[]'::jsonb)) AS value
                            WHERE trim(both '"' FROM value::text) <> :misplaced_link
                        ),
                        '[]'::jsonb
                    ),
                    true
                ),
                '{source_links,airbnb}',
                COALESCE(h.metadata->'source_links'->'airbnb', '[]'::jsonb)
                    || to_jsonb(ARRAY[:misplaced_link]::text[]),
                true
            ),
            '{canonical_links,airbnb}',
            to_jsonb(:misplaced_link::text),
            true
        ),
        '{google_place_id}',
        CASE
            WHEN COALESCE(:google_place_id, '') = '' THEN COALESCE(h.metadata->'google_place_id', 'null'::jsonb)
            ELSE to_jsonb(:google_place_id::text)
        END,
        true
    )
    WHERE h.id = CAST(:hotel_id AS uuid)
    RETURNING h.id
)
UPDATE hotels h
SET metadata = jsonb_set(
    COALESCE(h.metadata, '{}'::jsonb),
    '{airbnb_room_id}',
    CASE
        WHEN COALESCE(:airbnb_room_id, '') = '' THEN COALESCE(h.metadata->'airbnb_room_id', 'null'::jsonb)
        ELSE to_jsonb(:airbnb_room_id::text)
    END,
    true
)
WHERE h.id = CAST(:hotel_id AS uuid);

UPDATE hotel_platform_accounts hpa
SET
    platform_id = p.id,
    external_account_id = :misplaced_link,
    config = jsonb_set(
        jsonb_set(
            COALESCE(hpa.config, '{}'::jsonb),
            '{platform_code}',
            '"airbnb"'::jsonb,
            true
        ),
        '{canonical_link}',
        to_jsonb(:misplaced_link::text),
        true
    ),
    raw_payload = jsonb_set(
        jsonb_set(
            COALESCE(hpa.raw_payload, '{}'::jsonb),
            '{platform_code}',
            '"airbnb"'::jsonb,
            true
        ),
        '{canonical_link}',
        to_jsonb(:misplaced_link::text),
        true
    ),
    updated_at = now()
FROM platforms p
WHERE hpa.hotel_id = CAST(:hotel_id AS uuid)
  AND hpa.external_account_id = :misplaced_link
  AND p.platform_code = 'airbnb';

INSERT INTO hotel_platform_accounts (
    hotel_id,
    platform_id,
    external_account_id,
    display_name,
    account_status,
    sync_enabled,
    config,
    raw_payload
)
SELECT
    h.id,
    p.id,
    :misplaced_link,
    h.hotel_name,
    'active',
    true,
    jsonb_build_object(
        'source_link', :misplaced_link,
        'canonical_link', :misplaced_link,
        'platform_code', 'airbnb'
    ),
    jsonb_build_object(
        'source_link', :misplaced_link,
        'canonical_link', :misplaced_link,
        'platform_code', 'airbnb',
        'created_from', 'airbnb_google_db_repair'
    )
FROM hotels h
JOIN platforms p ON p.platform_code = 'airbnb'
WHERE h.id = CAST(:hotel_id AS uuid)
ON CONFLICT (hotel_id, platform_id, external_account_id) DO NOTHING;

COMMIT;

-- ============================================================
-- E. Verify 1 hotel sau khi fix
-- ============================================================

SELECT
    id,
    hotel_code,
    hotel_name,
    metadata->'source_links'->'google' AS google_links,
    metadata->'source_links'->'airbnb' AS airbnb_links,
    metadata->'canonical_links'->'airbnb' AS canonical_airbnb,
    metadata->'google_place_id' AS google_place_id,
    metadata->'airbnb_room_id' AS airbnb_room_id
FROM hotels
WHERE id = CAST(:hotel_id AS uuid);

SELECT
    hpa.id,
    p.platform_code,
    hpa.external_account_id,
    hpa.config,
    hpa.raw_payload
FROM hotel_platform_accounts hpa
JOIN platforms p ON p.id = hpa.platform_id
WHERE hpa.hotel_id = CAST(:hotel_id AS uuid)
ORDER BY p.platform_code, hpa.external_account_id;
