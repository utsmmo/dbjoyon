SET search_path TO public;

CREATE TABLE IF NOT EXISTS countries (
    code CHAR(2) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_hotel_scopes (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    can_edit_reviews BOOLEAN NOT NULL DEFAULT FALSE,
    can_edit_hotel BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, hotel_id)
);

ALTER TABLE hotels
    ADD COLUMN IF NOT EXISTS address TEXT,
    ADD COLUMN IF NOT EXISTS star_rating NUMERIC(3,1),
    ADD COLUMN IF NOT EXISTS brand_name VARCHAR(120),
    ADD COLUMN IF NOT EXISTS latitude NUMERIC(10,7),
    ADD COLUMN IF NOT EXISTS longitude NUMERIC(10,7),
    ADD COLUMN IF NOT EXISTS is_featured BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE reviews
    ADD COLUMN IF NOT EXISTS sentiment_score NUMERIC(6,3),
    ADD COLUMN IF NOT EXISTS ai_summary TEXT,
    ADD COLUMN IF NOT EXISTS ai_keywords JSONB NOT NULL DEFAULT '[]'::JSONB,
    ADD COLUMN IF NOT EXISTS ai_topics JSONB NOT NULL DEFAULT '[]'::JSONB,
    ADD COLUMN IF NOT EXISTS analysis_version VARCHAR(100),
    ADD COLUMN IF NOT EXISTS analysis_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_reviews_analysis_status'
    ) THEN
        ALTER TABLE reviews
            ADD CONSTRAINT chk_reviews_analysis_status
            CHECK (analysis_status IN ('pending', 'done', 'failed'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS review_analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100) NOT NULL,
    provider_name VARCHAR(100),
    model_name VARCHAR(120),
    model_version VARCHAR(120),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    request_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    response_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_review_analysis_runs_status CHECK (
        status IN ('pending', 'running', 'done', 'failed')
    )
);

CREATE TABLE IF NOT EXISTS review_tag_map (
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES review_tags(id) ON DELETE CASCADE,
    tagged_by VARCHAR(50) NOT NULL DEFAULT 'system',
    confidence_score NUMERIC(6,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (review_id, tag_id)
);

CREATE OR REPLACE VIEW review_sources AS
SELECT
    id,
    platform_code AS source_code,
    platform_name AS source_name,
    platform_type,
    is_active,
    metadata,
    created_at,
    updated_at
FROM platforms;

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

CREATE INDEX IF NOT EXISTS idx_hotels_country_code
    ON hotels (country_code);

CREATE INDEX IF NOT EXISTS idx_hotels_featured
    ON hotels (is_featured);

CREATE INDEX IF NOT EXISTS idx_reviews_rating
    ON reviews (rating);

CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_country_code
    ON reviews (reviewer_country_code);

CREATE INDEX IF NOT EXISTS idx_reviews_analysis_status
    ON reviews (analysis_status, analyzed_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_hotel_scopes_hotel_id
    ON user_hotel_scopes (hotel_id);

CREATE INDEX IF NOT EXISTS idx_review_analysis_runs_review_id
    ON review_analysis_runs (review_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_review_tag_map_tag_id
    ON review_tag_map (tag_id);

INSERT INTO countries (code, name)
VALUES
    ('VN', 'Vietnam'),
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('AU', 'Australia'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('KR', 'South Korea'),
    ('JP', 'Japan'),
    ('CN', 'China'),
    ('SG', 'Singapore')
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    updated_at = NOW();

INSERT INTO roles (code, name, description)
VALUES
    ('admin', 'Administrator', 'Toan quyen quan tri he thong'),
    ('manager', 'Manager', 'Quan ly du lieu khach san va review'),
    ('member', 'Member', 'Nguoi dung xem du lieu va van hanh co ban')
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO permissions (code, name, description)
VALUES
    ('hotel.view', 'View hotel', 'Xem thong tin khach san'),
    ('hotel.edit', 'Edit hotel', 'Cap nhat thong tin khach san'),
    ('review.view', 'View review', 'Xem review'),
    ('review.edit', 'Edit review', 'Cap nhat metadata review'),
    ('review.reply', 'Reply review', 'Quan ly phan hoi review'),
    ('dashboard.view', 'View dashboard', 'Xem dashboard va thong ke'),
    ('user.manage', 'Manage user', 'Quan ly tai khoan nguoi dung')
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON
    (r.code = 'admin')
    OR (r.code = 'manager' AND p.code IN ('hotel.view', 'hotel.edit', 'review.view', 'review.edit', 'review.reply', 'dashboard.view'))
    OR (r.code = 'member' AND p.code IN ('hotel.view', 'review.view', 'dashboard.view'))
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO users (email, password_hash, full_name, is_active)
VALUES
    ('admin@datac.click', crypt('Admin@123', gen_salt('bf', 12)), 'System Admin', TRUE),
    ('manager@datac.click', crypt('Manager@123', gen_salt('bf', 12)), 'Hotel Manager', TRUE),
    ('member@datac.click', crypt('Member@123', gen_salt('bf', 12)), 'Team Member', TRUE),
    ('ops.manager@datac.click', crypt('OpsManager@123', gen_salt('bf', 12)), 'Operations Manager', TRUE),
    ('review.member@datac.click', crypt('ReviewMember@123', gen_salt('bf', 12)), 'Review Team Member', TRUE)
ON CONFLICT (email) DO UPDATE
SET
    full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON
    (u.email = 'admin@datac.click' AND r.code = 'admin')
    OR (u.email = 'manager@datac.click' AND r.code = 'manager')
    OR (u.email = 'member@datac.click' AND r.code = 'member')
    OR (u.email = 'ops.manager@datac.click' AND r.code = 'manager')
    OR (u.email = 'review.member@datac.click' AND r.code = 'member')
ON CONFLICT (user_id, role_id) DO NOTHING;
