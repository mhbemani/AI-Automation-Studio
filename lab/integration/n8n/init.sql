-- fresh install schema. An existing DB was migrated with the ALTERs at the bottom (see report).
CREATE TABLE content_items (
  id serial PRIMARY KEY, topic text NOT NULL,
  status text NOT NULL DEFAULT 'IDEA' CHECK (status IN ('IDEA','SCRIPTING','RENDERING','AWAITING_APPROVAL','APPROVED','PUBLISHED','FAILED')),
  script jsonb, note text,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
-- ALTER TABLE content_items DROP CONSTRAINT content_items_status_check;
-- ALTER TABLE content_items ADD CONSTRAINT content_items_status_check CHECK (status IN ('IDEA','SCRIPTING','RENDERING','AWAITING_APPROVAL','APPROVED','PUBLISHED','FAILED')), ADD COLUMN note text;
