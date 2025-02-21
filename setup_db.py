from supabase import create_client

# Initialize Supabase client
supabase = create_client(
    "https://hripgasidctuxbpolzso.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhyaXBnYXNpZGN0dXhicG9senNvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzkwODUwMDcsImV4cCI6MjA1NDY2MTAwN30.Jep4DdjRUK7tiV1nrbDZfzX3DoXuXKl7TWndeQ1BsBY"
)

# SQL to create the table with the correct structure
create_table_sql = """
-- Drop the existing table if it exists
DROP TABLE IF EXISTS audio_responses;

-- Create the table with the correct structure
CREATE TABLE audio_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audio_recording TEXT,
    input_transcription TEXT,
    model_output TEXT,
    output_audio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable Row Level Security
ALTER TABLE audio_responses ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations
CREATE POLICY "Enable all operations for users"
    ON audio_responses
    FOR ALL
    TO public
    USING (true)
    WITH CHECK (true);
"""

print("Please run this SQL in your Supabase SQL editor:")
print(create_table_sql)

# Test the table structure
try:
    # Try to insert a test record
    test_data = {
        "audio_recording": "test_recording",
        "input_transcription": "test_transcription",
        "model_output": "test_output",
        "output_audio": "test_output_audio"
    }
    
    result = supabase.table("audio_responses").insert(test_data).execute()
    print("\nSuccessfully inserted test record with columns:")
    print(list(test_data.keys()))
    
    # Clean up test record
    supabase.table("audio_responses").delete().eq("audio_recording", "test_recording").execute()
    
except Exception as e:
    print(f"\nError: {str(e)}")
