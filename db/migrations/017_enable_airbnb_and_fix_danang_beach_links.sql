SET search_path TO public;

INSERT INTO platforms (platform_code, platform_name, platform_type, is_active, metadata)
VALUES ('airbnb', 'Airbnb', 'review', TRUE, '{"source":"migration_017"}'::jsonb)
ON CONFLICT (platform_code) DO UPDATE
SET
    platform_name = EXCLUDED.platform_name,
    platform_type = EXCLUDED.platform_type,
    is_active = TRUE,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();
