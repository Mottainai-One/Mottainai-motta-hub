-- Execute in the mottainai database. These are Hub metadata tables in public;
-- they do not create or alter operational business tables.
CREATE TABLE IF NOT EXISTS public.hub_documentation_catalog (
    id smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    schemas_json jsonb NOT NULL CHECK (jsonb_typeof(schemas_json) = 'array'),
    documents_json jsonb NOT NULL CHECK (jsonb_typeof(documents_json) = 'array'),
    updated_by_email text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.hub_table_catalog (
    table_id text PRIMARY KEY,
    schema_name text NOT NULL,
    table_name text NOT NULL,
    description text NOT NULL DEFAULT '',
    columns_json jsonb NOT NULL CHECK (jsonb_typeof(columns_json) = 'array'),
    is_deleted boolean NOT NULL DEFAULT false,
    updated_by_email text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

