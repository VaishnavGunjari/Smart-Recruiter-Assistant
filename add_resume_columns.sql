-- Add resume-related columns to the existing candidates table
ALTER TABLE candidates 
ADD COLUMN resume_path TEXT,
ADD COLUMN resume_summary TEXT,
ADD COLUMN skills TEXT;

-- Create GIN indexes for full-text search on resume fields
CREATE INDEX idx_candidates_resume_summary_gin ON candidates USING GIN (to_tsvector('english', resume_summary));
CREATE INDEX idx_candidates_skills_gin ON candidates USING GIN (to_tsvector('english', skills));

-- Add comments to document the new columns
COMMENT ON COLUMN candidates.resume_path IS 'Path to uploaded resume file';
COMMENT ON COLUMN candidates.resume_summary IS 'AI-generated summary of the resume';
COMMENT ON COLUMN candidates.skills IS 'JSON string of extracted skills from resume';