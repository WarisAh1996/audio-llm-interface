from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid
import logging
import whisper
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

# Global variables for Whisper model
model = None
model_lock = asyncio.Lock()
executor = ThreadPoolExecutor(max_workers=1)

async def load_whisper_model():
    """Load Whisper model asynchronously"""
    global model
    if model is None:
        async with model_lock:
            if model is None:  # Double-check pattern
                logger.info("Loading Whisper model (tiny)...")
                loop = asyncio.get_event_loop()
                model = await loop.run_in_executor(executor, whisper.load_model, "tiny")
                logger.info("Whisper model loaded successfully")
    return model

@app.post("/upload-audio")
async def upload_audio(audio_file: UploadFile = File(...)):
    try:
        logger.info("Received audio upload request")
        # Read the audio file
        contents = await audio_file.read()
        
        # Generate a unique ID for the audio file
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}.webm"
        
        try:
            # Upload the original WebM file to Supabase Storage
            logger.info("Uploading audio to Supabase Storage")
            storage_result = supabase.storage.from_("audio").upload(
                path=file_name,
                file=contents,
                file_options={"content-type": "audio/webm"}
            )
            
            # Get the public URL for the uploaded file
            audio_url = supabase.storage.from_("audio").get_public_url(file_name)
            logger.info("Audio uploaded successfully to storage: %s", audio_url)
            
            # Insert initial record into audio_responses table
            logger.info("Inserting record into audio_responses table")
            data = {
                "id": file_id,
                "audio_recording": audio_url,
                "input_transcription": None,
                "model_output": None,
                "output_audio": None
            }
            
            db_result = supabase.table("audio_responses").insert(data).execute()
            logger.info("Database record created successfully")
            
            # Start transcription process in background
            # Pass the original audio content to avoid downloading again
            asyncio.create_task(process_transcription(file_id, contents))
            
            return JSONResponse({
                "status": "success",
                "message": "Audio uploaded successfully, transcription in progress",
                "file_id": file_id,
                "audio_url": audio_url
            })
            
        except Exception as upload_error:
            logger.error("Upload error: %s", str(upload_error))
            return JSONResponse({
                "status": "error",
                "message": f"Error uploading to Supabase: {str(upload_error)}"
            }, status_code=500)
        
    except Exception as e:
        logger.error("General error: %s", str(e))
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

async def process_transcription(file_id: str, audio_data: bytes):
    """Process transcription using the original audio data"""
    temp_path = None
    try:
        # Save audio data to temporary file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()  # Ensure all data is written
            temp_path = temp_file.name
            logger.info(f"Audio saved to temporary file: {temp_path}")

        try:
            logger.info(f"Starting transcription for file {file_id}")
            
            # Ensure model is loaded
            model = await load_whisper_model()
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, model.transcribe, temp_path)
            transcription = result["text"]
            
            logger.info(f"Transcription completed for file {file_id}")
            
            # Update the database record with transcription
            supabase.table("audio_responses").update({
                "input_transcription": transcription
            }).eq("id", file_id).execute()
            
            logger.info(f"Database updated with transcription for file {file_id}")
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"Temporary file deleted: {temp_path}")
                
    except Exception as e:
        logger.error(f"Error in transcription process for file {file_id}: {str(e)}")
        # Update database with error
        try:
            supabase.table("audio_responses").update({
                "input_transcription": f"Error during transcription: {str(e)}"
            }).eq("id", file_id).execute()
        except:
            pass

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# Start loading the model when the server starts
@app.on_event("startup")
async def startup_event():
    logger.info("Starting server...")
    # Start loading the model in the background
    asyncio.create_task(load_whisper_model())
