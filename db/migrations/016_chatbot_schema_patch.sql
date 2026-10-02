SET search_path TO public;

ALTER TABLE IF EXISTS chatbot_feedback_learning
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
