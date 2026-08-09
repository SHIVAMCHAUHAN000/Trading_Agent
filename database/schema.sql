-- Supabase / Postgres schema sketch (Stage 2)
-- Not applied yet — wait for DATABASE_URL credentials.

-- Experiments registry (failures included)
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id   TEXT PRIMARY KEY,          -- EXP-000001
    strategy_name   TEXT NOT NULL,
    request_json    JSONB NOT NULL,
    data_version    TEXT,
    code_version    TEXT,
    researcher      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          TEXT NOT NULL,             -- RUNNING | FAILED | COMPLETE
    conclusion      TEXT,                      -- REJECT | INCONCLUSIVE | PROMISING | VALIDATED_CANDIDATE
    results_json    JSONB,
    warnings_json   JSONB
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id     TEXT PRIMARY KEY,          -- MOM-001
    name            TEXT NOT NULL,
    version         TEXT NOT NULL,
    status          TEXT NOT NULL,             -- IDEA | BACKTEST | VALIDATION | APPROVED | REJECTED
    spec_json       JSONB NOT NULL,
    latest_experiment_id TEXT REFERENCES experiments(experiment_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_data_catalog (
    dataset_id      TEXT PRIMARY KEY,
    source          TEXT NOT NULL,             -- yfinance
    universe_id     TEXT NOT NULL,             -- NIFTY50
    history_start   DATE,
    history_end     DATE,
    adjusted        BOOLEAN DEFAULT TRUE,
    raw_path        TEXT,                      -- local parquet/raw pointer
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Raw vendor dumps stay on disk under data/raw/ (immutable).
-- Postgres stores catalog + experiment metadata first; bar storage can come later.
