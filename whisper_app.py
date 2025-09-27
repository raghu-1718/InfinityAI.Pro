from fastapi import FastAPI, File, UploadFile
import whisper
import torch
import io

app = FastAPI(title="Whisper Speech-to-Text API")

# Load Whisper model
model = whisper.load_model("base")  # You can use "tiny", "base", "small", "medium", "large"

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio file to text
    """
    try:
        # Save uploaded file temporarily
        contents = await file.read()

        # Write to temporary file
        temp_path = "/tmp/audio.wav"
        with open(temp_path, "wb") as f:
            f.write(contents)

        # Transcribe
        result = model.transcribe(temp_path)

        # Clean up
        import os
        os.remove(temp_path)

        return {
            "text": result["text"],
            "language": result["language"],
            "segments": result["segments"]
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Whisper Speech-to-Text API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)