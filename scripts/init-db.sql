-- init-db.sql
-- FlyReady Lab - Database Initialization Script
-- Enterprise-grade PostgreSQL setup

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS flyready;

-- Set default schema
SET search_path TO flyready, public;

-- =============================================================================
-- Users Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    profile_image VARCHAR(500),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'mentor', 'admin')),
    subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'premium', 'enterprise')),
    subscription_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users USING btree (email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users USING btree (role);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users USING btree (subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users USING btree (created_at DESC);

-- =============================================================================
-- Interview Sessions Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL,
    airline_name VARCHAR(100),
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,
    overall_score DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'created' CHECK (status IN ('created', 'in_progress', 'completed', 'cancelled')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user ON interview_sessions USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON interview_sessions USING btree (status);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON interview_sessions USING btree (created_at DESC);

-- =============================================================================
-- Interview Questions Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),
    time_limit INTEGER DEFAULT 60,
    tips TEXT,
    answer TEXT,
    answer_duration DECIMAL(10,2),
    feedback JSONB,
    score DECIMAL(5,2),
    asked_at TIMESTAMP,
    answered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Question indexes
CREATE INDEX IF NOT EXISTS idx_questions_session ON interview_questions USING btree (session_id);

-- =============================================================================
-- Payments Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'KRW',
    payment_method VARCHAR(50) NOT NULL,
    payment_provider VARCHAR(50),
    transaction_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded', 'cancelled')),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment indexes
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments USING btree (status);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments USING btree (created_at DESC);

-- =============================================================================
-- Subscriptions Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    billing_cycle VARCHAR(20) DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'yearly')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'paused')),
    starts_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    cancelled_at TIMESTAMP,
    auto_renew BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscription indexes
CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions USING btree (status);
CREATE INDEX IF NOT EXISTS idx_subs_expires ON subscriptions USING btree (expires_at);

-- =============================================================================
-- Mentors Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS mentors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    title VARCHAR(200),
    bio TEXT,
    profile_image VARCHAR(500),
    specializations TEXT[],
    experience_years INTEGER DEFAULT 0,
    airline_experience TEXT[],
    rating DECIMAL(3,2) DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    hourly_rate DECIMAL(10,2),
    is_available BOOLEAN DEFAULT true,
    availability JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mentor indexes
CREATE INDEX IF NOT EXISTS idx_mentors_rating ON mentors USING btree (rating DESC);
CREATE INDEX IF NOT EXISTS idx_mentors_available ON mentors USING btree (is_available);
CREATE INDEX IF NOT EXISTS idx_mentors_specializations ON mentors USING gin (specializations);

-- =============================================================================
-- Mentor Sessions Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS mentor_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mentor_id UUID NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show')),
    meeting_url VARCHAR(500),
    notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mentor session indexes
CREATE INDEX IF NOT EXISTS idx_mentor_sessions_mentor ON mentor_sessions USING btree (mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_sessions_user ON mentor_sessions USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_sessions_scheduled ON mentor_sessions USING btree (scheduled_at);

-- =============================================================================
-- Job Postings Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS job_postings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    airline_name VARCHAR(100) NOT NULL,
    airline_logo VARCHAR(500),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    requirements TEXT[],
    qualifications TEXT[],
    benefits TEXT[],
    location VARCHAR(200),
    employment_type VARCHAR(50),
    salary_range VARCHAR(100),
    application_url VARCHAR(500),
    application_deadline TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    view_count INTEGER DEFAULT 0,
    apply_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job posting indexes
CREATE INDEX IF NOT EXISTS idx_jobs_airline ON job_postings USING btree (airline_name);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON job_postings USING btree (is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_deadline ON job_postings USING btree (application_deadline);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON job_postings USING btree (created_at DESC);

-- =============================================================================
-- Notifications Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications USING btree (is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications USING btree (created_at DESC);

-- =============================================================================
-- User Activity Logs Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity log indexes
CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity_logs USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_action ON user_activity_logs USING btree (action);
CREATE INDEX IF NOT EXISTS idx_activity_created ON user_activity_logs USING btree (created_at DESC);

-- =============================================================================
-- Functions and Triggers
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON interview_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mentors_updated_at BEFORE UPDATE ON mentors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mentor_sessions_updated_at BEFORE UPDATE ON mentor_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON job_postings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Initial Admin User
-- =============================================================================
INSERT INTO users (email, password_hash, name, role, subscription_tier, is_active, is_verified)
VALUES (
    'admin@flyreadylab.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.i5uIGAn8EQbK6G', -- password: admin123
    'System Admin',
    'admin',
    'enterprise',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA flyready TO flyready;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA flyready TO flyready;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'FlyReady Lab database initialized successfully!';
END $$;
