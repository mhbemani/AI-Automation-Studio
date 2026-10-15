-- fresh install schema. An existing lab DB is migrated with migrate_asset_generation.sql.
CREATE TABLE content_items (
  id serial PRIMARY KEY, topic text NOT NULL,
  status text NOT NULL DEFAULT 'IDEA' CHECK (status IN ('IDEA','SCRIPTING','ASSET_GENERATION','RENDERING','AWAITING_APPROVAL','APPROVED','PUBLISHED','FAILED')),
  script jsonb, note text,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
