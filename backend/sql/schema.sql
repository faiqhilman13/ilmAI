-- IlmuAI Database Schema
-- PostgreSQL with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Knowledge Sources table
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL, -- 'quran', 'hadith', 'fiqh', 'fatwa'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge Chunks table (with vector embedding)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES knowledge_sources(id) ON DELETE SET NULL,
    source_type VARCHAR(50) NOT NULL,
    text_content TEXT NOT NULL,
    text_arabic TEXT,
    text_translation TEXT,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    chunk_metadata JSONB NOT NULL DEFAULT '{}',
    chunk_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for vector similarity search (IVFFlat for performance)
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding
ON knowledge_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for filtering by source type
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_type
ON knowledge_chunks(source_type);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'ms',
    preferred_madhab VARCHAR(50) DEFAULT 'shafii',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for email lookup
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ms',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for user conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    citations JSONB, -- Array of citation objects
    disclaimer TEXT,
    topics TEXT[], -- Detected topics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for conversation messages
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Bookmarks table
CREATE TABLE IF NOT EXISTS bookmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    note TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, message_id)
);

-- Index for user bookmarks
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default knowledge sources
INSERT INTO knowledge_sources (source_type, name, description, source_metadata) VALUES
    ('quran', 'Al-Quran', 'The Holy Quran with Uthmani script and translations', '{"translations": ["ms.basmeih", "en.sahih"]}'),
    ('hadith', 'Sahih al-Bukhari', 'Collection of hadith by Imam Bukhari', '{"grading": "sahih"}'),
    ('hadith', 'Sahih Muslim', 'Collection of hadith by Imam Muslim', '{"grading": "sahih"}'),
    ('hadith', 'Sunan Abu Dawud', 'Collection of hadith by Imam Abu Dawud', '{"grading": "mixed"}'),
    ('hadith', 'Jami at-Tirmidhi', 'Collection of hadith by Imam Tirmidhi', '{"grading": "mixed"}'),
    ('hadith', 'Sunan an-Nasai', 'Collection of hadith by Imam Nasai', '{"grading": "mixed"}'),
    ('hadith', 'Sunan Ibn Majah', 'Collection of hadith by Imam Ibn Majah', '{"grading": "mixed"}'),
    ('fiqh', 'Al-Fiqh Al-Manhaji (Shafii)', 'Systematic Shafii fiqh manual - JAKIM edition', '{"madhab": "shafii", "language": "ms"}'),
    ('fatwa', 'e-Fatwa JAKIM', 'Official Malaysian fatwa database', '{"authority": "JAKIM", "country": "Malaysia"}')
ON CONFLICT DO NOTHING;
