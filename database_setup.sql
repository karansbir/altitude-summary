-- Database schema for Altitude Summary
-- Run this in your Supabase SQL editor

-- Create activities table
CREATE TABLE IF NOT EXISTS activities (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  date DATE NOT NULL,
  activity_type VARCHAR(50) NOT NULL, -- 'toileting', 'diaper', 'nap', 'meal', 'other'
  activity_subtype VARCHAR(50), -- 'wet', 'dry', 'bm', 'start', 'stop', 'all', 'some', 'none'
  activity_name VARCHAR(100), -- 'AM Snack', 'Lunch', 'PM Snack', or custom activity names
  raw_content TEXT, -- original message content for debugging
  parsed_time VARCHAR(20), -- time from email (e.g., "2:30 PM")
  source_message_id VARCHAR(255), -- Gmail message ID
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date);
CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp);
CREATE INDEX IF NOT EXISTS idx_activities_source_message ON activities(source_message_id);

-- Create a view for easy querying of daily summaries
CREATE OR REPLACE VIEW daily_activity_summary AS
SELECT 
  date,
  COUNT(*) as total_activities,
  COUNT(CASE WHEN activity_type = 'toileting' THEN 1 END) as toileting_count,
  COUNT(CASE WHEN activity_type = 'diaper' THEN 1 END) as diaper_count,
  COUNT(CASE WHEN activity_type = 'nap' THEN 1 END) as nap_count,
  COUNT(CASE WHEN activity_type = 'meal' THEN 1 END) as meal_count,
  COUNT(CASE WHEN activity_type = 'other' THEN 1 END) as other_count
FROM activities
GROUP BY date
ORDER BY date DESC;

-- Create a function to get activities for a specific date
CREATE OR REPLACE FUNCTION get_activities_by_date(target_date DATE)
RETURNS TABLE (
  id INTEGER,
  activity_timestamp TIMESTAMP WITH TIME ZONE,
  activity_date DATE,
  activity_type VARCHAR(50),
  activity_subtype VARCHAR(50),
  activity_name VARCHAR(100),
  raw_content TEXT,
  parsed_time VARCHAR(20),
  source_message_id VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT a.id, a.timestamp, a.date, a.activity_type, a.activity_subtype, 
         a.activity_name, a.raw_content, a.parsed_time, a.source_message_id, a.created_at
  FROM activities a
  WHERE a.date = target_date
  ORDER BY a.timestamp;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security (RLS) - Optional, for security
-- ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

-- Create a policy for authenticated users (uncomment if using RLS)
-- CREATE POLICY "Users can view all activities" ON activities
--   FOR SELECT USING (auth.role() = 'authenticated');

-- Create a policy for service role to insert (uncomment if using RLS)  
-- CREATE POLICY "Service role can insert activities" ON activities
--   FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Sample query to test the setup
-- SELECT * FROM daily_activity_summary LIMIT 10;