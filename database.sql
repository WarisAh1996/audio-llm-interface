-- Create the audio_responses table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.audio_responses (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    audio_path text NOT NULL,
    transcription text,
    model_output text,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- Enable Row Level Security
ALTER TABLE public.audio_responses ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for all users
CREATE POLICY "Enable all access for all users"
    ON public.audio_responses
    FOR ALL
    TO public
    USING (true)
    WITH CHECK (true);

-- Grant all privileges to public
GRANT ALL ON public.audio_responses TO public;
