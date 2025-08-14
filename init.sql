-- init-db.sql
-- Create the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a schema for our telecom documents
CREATE SCHEMA IF NOT EXISTS telecom;

-- Create the collection table for LangChain
CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    name VARCHAR(255) PRIMARY KEY,
    cmetadata JSON,
    uuid UUID NOT NULL DEFAULT gen_random_uuid()
);

-- Create the embedding table for LangChain
CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE CASCADE,
    embedding VECTOR(1536), -- OpenAI embeddings are 1536 dimensions
    document TEXT,
    cmetadata JSON,
    custom_id VARCHAR(255)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_embedding_collection_id ON langchain_pg_embedding(collection_id);
CREATE INDEX IF NOT EXISTS idx_embedding_vector ON langchain_pg_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Insert default collection
INSERT INTO langchain_pg_collection (name, cmetadata)
VALUES ('telecom_docs', '{"description": "Telecom FAQ and documentation"}')
ON CONFLICT (name) DO NOTHING;

-- Sample telecom documents (you can add your own)
WITH collection_uuid AS (
    SELECT uuid FROM langchain_pg_collection WHERE name = 'telecom_docs'
)
INSERT INTO langchain_pg_embedding (collection_id, document, cmetadata, custom_id)
SELECT
    collection_uuid.uuid,
    doc.content,
    doc.metadata::json,
    doc.id
FROM collection_uuid,
(VALUES
    ('doc_1', 'Şirketimizde Bronze, Silver, Gold ve Platinum paketleri bulunmaktadır. Bronze paket ayda 59.90 TL, 5GB internet, 500 dakika konuşma içerir.', '{"source": "packages.pdf", "page": 1}'),
    ('doc_2', 'Gold paket ayda 79.90 TL, 20GB internet, sınırsız konuşma ve 1000 SMS içerir. En popüler paketimizdir.', '{"source": "packages.pdf", "page": 2}'),
    ('doc_3', 'Müşteri hizmetlerimiz 7/24 açıktır. 444 0 123 numarasından bize ulaşabilirsiniz.', '{"source": "contact.pdf", "page": 1}'),
    ('doc_4', 'Fatura ödeme son tarihi her ayın 15''idir. Kredi kartı, banka kartı veya havale ile ödeme yapabilirsiniz.', '{"source": "billing.pdf", "page": 1}'),
    ('doc_5', 'Roaming hizmetleri Avrupa''da günlük 15 TL, ABD''de günlük 25 TL''dir. Roaming''i aktif etmek için *123# tuşlayın.', '{"source": "roaming.pdf", "page": 1}'),
    ('doc_6', 'İnternet kotanız bittiğinde hız 128 kbps''ye düşer. Ek internet paketi 5GB için 15 TL''den satın alabilirsiniz.', '{"source": "internet.pdf", "page": 1}'),
    ('doc_7', 'Hat kapama işlemi için müşteri hizmetlerini arayın. Kapama ücreti 10 TL''dir.', '{"source": "services.pdf", "page": 1}'),
    ('doc_8', 'Yeni hat açma için kimlik belgesi, ikametgah belgesi ve banka bilgileri gereklidir.', '{"source": "registration.pdf", "page": 1}')
) AS doc(id, content, metadata)
ON CONFLICT (custom_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO telecom_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO telecom_user;