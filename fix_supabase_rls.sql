-- Option 1: Disable RLS for development (NOT recommended for production)
-- ALTER TABLE candidates DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE interview_questions DISABLE ROW LEVEL SECURITY;

-- Option 2: Create policies to allow all operations (for development)
-- Enable RLS if not already enabled
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_questions ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Enable all operations for candidates" ON candidates;
DROP POLICY IF EXISTS "Enable all operations for interview_questions" ON interview_questions;

-- Create permissive policies for development
CREATE POLICY "Enable all operations for candidates" ON candidates
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Enable all operations for interview_questions" ON interview_questions
    FOR ALL USING (true) WITH CHECK (true);

-- Refresh the schema cache
NOTIFY pgrst, 'reload schema';