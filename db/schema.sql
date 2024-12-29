-- Enable vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create items table if it doesn't exist
CREATE TABLE IF NOT EXISTS items (
    id bigserial PRIMARY KEY,
    embedding vector(3)
); 
