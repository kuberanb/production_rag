-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table
CREATE TABLE IF NOT EXISTS documents(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_document_status
         CHECK(status IN (
                'pending',
                'processing',
                'completed',
                'failed'
         )),
    CONSTRAINT ck_documents_chunk_count
         CHECK(chunk_count >= 0)
);

-- Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_document_chunks_document
         FOREIGN KEY (document_id)
         REFERENCES documents(id)
         ON DELETE CASCADE,
    CONSTRAINT uq_document_chunks_doument_index
         UNIQUE(document_id,chunk_index),
    CONSTRAINT ck_document_chunks_index
        CHECK (chunk_index >= 0)
);

-- Index for document filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
ON document_chunks(document_id);

-- Index for document status filtering
CREATE INDEX IF NOT EXISTS ix_documents_status
ON documents(status);
