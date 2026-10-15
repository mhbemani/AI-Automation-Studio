CREATE TABLE content_items (
  id         serial PRIMARY KEY,
  topic      text NOT NULL,
  status     text NOT NULL DEFAULT 'IDEA'
    CHECK (status IN ('IDEA','SCRIPTING','RENDERING','AWAITING_APPROVAL','APPROVED','PUBLISHED')),
  script     jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
