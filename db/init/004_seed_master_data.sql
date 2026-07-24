SET search_path TO public;

INSERT INTO platforms (platform_code, platform_name, platform_type, is_active, metadata)
VALUES
    ('booking', 'Booking.com', 'review', TRUE, '{"source":"seed"}'::JSONB),
    ('agoda', 'Agoda', 'review', TRUE, '{"source":"seed"}'::JSONB),
    ('tripadvisor', 'Tripadvisor', 'review', TRUE, '{"source":"seed"}'::JSONB),
    ('google', 'Google Reviews', 'review', TRUE, '{"source":"seed"}'::JSONB)
ON CONFLICT (platform_code) DO UPDATE
SET
    platform_name = EXCLUDED.platform_name,
    platform_type = EXCLUDED.platform_type,
    is_active = EXCLUDED.is_active,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();
