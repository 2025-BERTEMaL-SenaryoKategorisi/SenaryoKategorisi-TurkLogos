-- PostgreSQL initialization script for PGVector telecom database
-- This script sets up the database with proper extensions and permissions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database user if not exists (for manual setup)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'telecom_user') THEN
        CREATE ROLE telecom_user WITH LOGIN PASSWORD '4Lt0g';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE telecom_vectordb TO telecom_user;
GRANT ALL ON SCHEMA public TO telecom_user;

-- Create tables for LangChain PGVector (if they don't exist)
-- These will be created automatically by langchain-postgres, but we can prepare the schema

-- Ensure proper permissions for vector operations
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO telecom_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO telecom_user;

-- Create index for better performance (will be created by langchain-postgres automatically)
-- But we can prepare for custom indexes if needed

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PGVector database initialized successfully for telecom agent';
END
$$;