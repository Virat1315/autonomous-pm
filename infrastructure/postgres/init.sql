-- Autonomous PM – PostgreSQL initialization
-- Runs once when the postgres container first starts

\connect autonomous_pm;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- The actual schema is created by SQLAlchemy on ticket-service startup (init_db).
-- This file is here for any seed data or manual schema additions.

-- Seed a default project
INSERT INTO tickets (title, description, ticket_type, status, priority, source)
SELECT 'Welcome to Autonomous PM', 'This is your first ticket. Create more from the dashboard or via Slack.', 'task', 'Open', 'Low', 'api'
WHERE NOT EXISTS (SELECT 1 FROM tickets LIMIT 1);
