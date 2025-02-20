from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid
import io
import numpy as np
import sys

# Add the psychology-alpaca model directory to path
sys.path.append(r"C:\Users\Waris\psychology-alpaca")

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

@app.post("/upload-audio")
async def upload_audio(audio_file: UploadFile = File(...)):
    try:
        # Read the audio file
        contents = await audio_file.read()
        
        # Generate a unique ID for the audio file
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}.webm"
        
        try:
            # Upload the original WebM file
            result = supabase.storage.from_("audio").upload(
                path=file_name,
                file=contents,
                file_options={"content-type": "audio/webm"}
            )
            
            # Get the public URL for the uploaded file
            audio_url = supabase.storage.from_("audio").get_public_url(file_name)
            
        except Exception as upload_error:
            print(f"Upload error: {str(upload_error)}")
            return JSONResponse({
                "status": "error",
                "message": f"Error uploading to Supabase: {str(upload_error)}"
            }, status_code=500)
        
        # For now, we'll just pass a placeholder audio data to the model
        # When integrating with your model, you'll need to properly process the WebM audio
        audio_data = np.zeros(1000)  # placeholder
        
        # Process audio with the LLM model
        model_output = process_with_llm(audio_data)
        
        # Store the results in Supabase Database
        data = {
            "id": file_id,
            "audio_path": audio_url,
            "model_output": model_output,
            "created_at": "now()"
        }
        
        try:
            result = supabase.table("audio_responses").insert(data).execute()
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            # Even if database insert fails, we'll return success since the file was uploaded
            return JSONResponse({
                "status": "partial_success",
                "message": "Audio uploaded but database update failed",
                "file_id": file_id,
                "model_output": model_output
            })
        
        return JSONResponse({
            "status": "success",
            "file_id": file_id,
            "model_output": model_output,
            "audio_url": audio_url
        })
        
    except Exception as e:
        print(f"General error: {str(e)}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

def process_with_llm(audio_data):
    # TODO: Implement the actual integration with your psychology-alpaca model
    # This is where you'll need to:
    # 1. Preprocess the audio data as required by your model
    # 2. Load and run your trained model
    # 3. Return the model's output
    
    # Placeholder return
    return "Audio received successfully! Model integration pending."

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
