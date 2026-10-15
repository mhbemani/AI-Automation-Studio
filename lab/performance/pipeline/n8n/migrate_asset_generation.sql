-- migration for an EXISTING lab DB (init.sql above already has it for fresh installs): allow the new ASSET_GENERATION status
ALTER TABLE content_items DROP CONSTRAINT IF EXISTS content_items_status_check;
ALTER TABLE content_items ADD CONSTRAINT content_items_status_check CHECK (status IN ('IDEA','SCRIPTING','ASSET_GENERATION','RENDERING','AWAITING_APPROVAL','APPROVED','PUBLISHED','FAILED'));
