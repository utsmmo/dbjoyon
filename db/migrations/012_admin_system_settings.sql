SET search_path TO public;

CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(120) NOT NULL UNIQUE,
    group_code VARCHAR(60) NOT NULL,
    label VARCHAR(120) NOT NULL,
    description TEXT,
    value_text TEXT,
    value_type VARCHAR(30) NOT NULL DEFAULT 'string',
    is_secret BOOLEAN NOT NULL DEFAULT FALSE,
    is_editable BOOLEAN NOT NULL DEFAULT TRUE,
    updated_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_system_settings_value_type CHECK (
        value_type IN ('string', 'secret', 'url', 'integer')
    )
);

CREATE INDEX IF NOT EXISTS idx_system_settings_group_code
    ON system_settings (group_code, setting_key);
