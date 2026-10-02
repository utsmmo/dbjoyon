BEGIN;

ALTER TABLE system_settings
    DROP CONSTRAINT IF EXISTS chk_system_settings_value_type;

ALTER TABLE system_settings
    ADD CONSTRAINT chk_system_settings_value_type CHECK (
        value_type IN ('string', 'secret', 'url', 'integer', 'float')
    );

INSERT INTO system_settings (
    setting_key,
    group_code,
    label,
    description,
    value_text,
    value_type,
    is_secret,
    is_editable
)
VALUES
    (
        'review.rating_band_average_min',
        'review',
        'Average review min score',
        'Nguong diem toi thieu de xep review vao nhom Average tren thang 10.',
        '7',
        'float',
        FALSE,
        TRUE
    ),
    (
        'review.rating_band_good_min',
        'review',
        'Good review min score',
        'Nguong diem toi thieu de xep review vao nhom Good tren thang 10.',
        '9',
        'float',
        FALSE,
        TRUE
    )
ON CONFLICT (setting_key) DO UPDATE
SET
    group_code = EXCLUDED.group_code,
    label = EXCLUDED.label,
    description = EXCLUDED.description,
    value_type = EXCLUDED.value_type,
    is_secret = EXCLUDED.is_secret,
    is_editable = EXCLUDED.is_editable;

COMMIT;
