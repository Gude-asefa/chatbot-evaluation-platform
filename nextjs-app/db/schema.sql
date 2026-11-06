-- Reference schema (matches the existing Streamlit/SQLAlchemy tables).
-- Only needed for a brand-new database; the existing Neon database already has these.
CREATE TABLE IF NOT EXISTS questions (
  id              SERIAL PRIMARY KEY,
  department      VARCHAR(100) NOT NULL,
  section         VARCHAR(100) NOT NULL,
  category        VARCHAR(150) NOT NULL,
  question_id     VARCHAR(50)  NOT NULL UNIQUE,
  question_type   VARCHAR(50)  NOT NULL,
  language        VARCHAR(50)  NOT NULL,
  question_text   TEXT         NOT NULL,
  expected_answer TEXT,
  is_active       BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS evaluations (
  id            SERIAL PRIMARY KEY,
  question_id   INTEGER NOT NULL REFERENCES questions(id),
  actual_answer TEXT,
  status        VARCHAR(50) NOT NULL,
  comments      TEXT,
  session_id    VARCHAR(100),
  submitted_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS submissions (
  id           SERIAL PRIMARY KEY,
  device_id    VARCHAR(100) NOT NULL,
  department   VARCHAR(100) NOT NULL,
  section      VARCHAR(100) NOT NULL,
  language     VARCHAR(50)  NOT NULL,
  submitted_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT uq_submission_device_section_language
    UNIQUE (device_id, department, section, language)
);
CREATE INDEX IF NOT EXISTS ix_submissions_device_id ON submissions (device_id);
