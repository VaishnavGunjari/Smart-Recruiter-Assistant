-- Create interview_reports table for storing comprehensive AI analysis
CREATE TABLE interview_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id VARCHAR(255) NOT NULL,
    candidate_name VARCHAR(255) NOT NULL,
    position VARCHAR(255) NOT NULL,
    interview_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- AI Analysis Scores (1-10 scale)
    communication_score INTEGER CHECK (communication_score >= 1 AND communication_score <= 10),
    technical_score INTEGER CHECK (technical_score >= 1 AND technical_score <= 10),
    soft_skills_score INTEGER CHECK (soft_skills_score >= 1 AND soft_skills_score <= 10),
    overall_score INTEGER CHECK (overall_score >= 1 AND overall_score <= 10),
    
    -- Full AI Analysis Report
    full_analysis_report TEXT NOT NULL,
    
    -- Structured Analysis Components
    strengths JSONB, -- Array of strengths with examples
    areas_for_improvement JSONB, -- Array of improvement areas
    technical_competencies JSONB, -- Array of technical skills assessed
    hiring_recommendation VARCHAR(50) CHECK (hiring_recommendation IN ('Strong Hire', 'Hire', 'Maybe', 'No Hire')),
    cultural_fit_analysis TEXT,
    salary_recommendation TEXT,
    next_steps TEXT,
    
    -- Metadata
    total_questions INTEGER DEFAULT 0,
    interview_duration_minutes INTEGER,
    report_generated_by VARCHAR(100) DEFAULT 'AI_System',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_candidate_id FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

-- Create indexes for efficient searching
CREATE INDEX idx_interview_reports_candidate_name ON interview_reports(candidate_name);
CREATE INDEX idx_interview_reports_position ON interview_reports(position);
CREATE INDEX idx_interview_reports_overall_score ON interview_reports(overall_score DESC);
CREATE INDEX idx_interview_reports_hiring_recommendation ON interview_reports(hiring_recommendation);
CREATE INDEX idx_interview_reports_interview_date ON interview_reports(interview_date DESC);

-- Create composite index for candidate search
CREATE INDEX idx_interview_reports_search ON interview_reports(candidate_name, position, overall_score DESC);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_interview_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_interview_reports_updated_at
    BEFORE UPDATE ON interview_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_interview_reports_updated_at();

-- Create view for report summary
CREATE OR REPLACE VIEW interview_reports_summary AS
SELECT 
    report_id,
    candidate_name,
    position,
    interview_date,
    communication_score,
    technical_score,
    soft_skills_score,
    overall_score,
    hiring_recommendation,
    total_questions,
    created_at,
    -- Calculate performance rating
    CASE 
        WHEN overall_score >= 9 THEN 'Exceptional'
        WHEN overall_score >= 8 THEN 'Excellent'
        WHEN overall_score >= 7 THEN 'Good'
        WHEN overall_score >= 6 THEN 'Fair'
        ELSE 'Needs Improvement'
    END as performance_rating,
    -- Calculate average skill score
    ROUND((communication_score + technical_score + soft_skills_score) / 3.0, 1) as avg_skill_score
FROM interview_reports
ORDER BY interview_date DESC;

-- Grant permissions (adjust as needed for your security setup)
-- Note: You may need to adjust these permissions based on your RLS policies
GRANT ALL ON interview_reports TO authenticated;
GRANT ALL ON interview_reports_summary TO authenticated;