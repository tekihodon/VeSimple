-- VeSimple Ticket Booking — schema for "9 Giờ Kém 15" liveshow
-- All tables prefixed with 9hkem15_ (must be quoted because starts with digit)

CREATE TABLE IF NOT EXISTS "9hkem15_tiers" (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    price       BIGINT NOT NULL,
    color       TEXT,
    sort_order  INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "9hkem15_seats" (
    id         BIGSERIAL PRIMARY KEY,
    code       TEXT UNIQUE NOT NULL,
    tier_id    TEXT NOT NULL REFERENCES "9hkem15_tiers"(id),
    row_id     TEXT NOT NULL,
    pos_x      REAL NOT NULL,
    pos_z      REAL NOT NULL,
    rot_y      REAL NOT NULL DEFAULT 0,
    side       TEXT,
    status     TEXT NOT NULL DEFAULT 'available'
                CHECK (status IN ('available','held','assigned')),
    order_id   BIGINT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS "9hkem15_seats_status_idx" ON "9hkem15_seats"(status);
CREATE INDEX IF NOT EXISTS "9hkem15_seats_tier_idx"   ON "9hkem15_seats"(tier_id);
CREATE INDEX IF NOT EXISTS "9hkem15_seats_order_idx"  ON "9hkem15_seats"(order_id);

CREATE TABLE IF NOT EXISTS "9hkem15_orders" (
    id          BIGSERIAL PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    full_name   TEXT NOT NULL,
    phone       TEXT NOT NULL,
    email       TEXT NOT NULL,
    total       BIGINT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending_payment'
                CHECK (status IN ('pending_payment','paid','cancelled','assigned')),
    items       JSONB NOT NULL,
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at     TIMESTAMPTZ,
    assigned_at TIMESTAMPTZ,
    email_sent_at TIMESTAMPTZ,
    email_sent_seats TEXT
);

CREATE INDEX IF NOT EXISTS "9hkem15_orders_status_idx" ON "9hkem15_orders"(status);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = '9hkem15_seats_order_fk'
    ) THEN
        ALTER TABLE "9hkem15_seats"
            ADD CONSTRAINT "9hkem15_seats_order_fk"
            FOREIGN KEY (order_id) REFERENCES "9hkem15_orders"(id) ON DELETE SET NULL;
    END IF;
END $$;
