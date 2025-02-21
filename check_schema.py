from supabase import create_client

# Initialize Supabase client
supabase = create_client(
    "https://hripgasidctuxbpolzso.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhyaXBnYXNpZGN0dXhicG9senNvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzkwODUwMDcsImV4cCI6MjA1NDY2MTAwN30.Jep4DdjRUK7tiV1nrbDZfzX3DoXuXKl7TWndeQ1BsBY"
)

try:
    # Try to insert a test record to see which columns exist
    test_data = {
        "audio_path": "test_path",
        "audio_recording": "test_recording",
        "transcription": "test_transcription",
        "model_output": "test_output"
    }
    
    result = supabase.table("audio_responses").insert(test_data).execute()
    print("Successfully inserted test record. Available columns:")
    print(test_data.keys())
    
    # Clean up test record
    supabase.table("audio_responses").delete().eq("audio_path", "test_path").execute()
    
except Exception as e:
    print(f"Error: {str(e)}")
    # Parse the error to understand which columns don't exist
    error_msg = str(e)
    if "column" in error_msg and "does not exist" in error_msg:
        print("\nMissing column detected in error message")
