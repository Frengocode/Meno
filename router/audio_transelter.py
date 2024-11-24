from fastapi import APIRouter, HTTPException, UploadFile, File
import aiofiles
import os
from pydub import AudioSegment
import speech_recognition as sr

audio_router = APIRouter(tags=["Audio to Text"])

UPLOAD_DIR = "media/"

@audio_router.post("/audio-text/")
async def audio_to_text(file: UploadFile = File(...)):
    temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
    wav_file_path = None
    
    try:
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        wav_file_path = convert_to_wav(temp_file_path)

        text = recognize_audio(wav_file_path)

        if text is None:
            raise HTTPException(status_code=500, detail="Failed to recognize speech")
        else:
            return {"text": text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Remove the temporary files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if wav_file_path and os.path.exists(wav_file_path):
            os.remove(wav_file_path)

def convert_to_wav(file_path: str) -> str:
    """Convert audio file to WAV format."""
    wav_file_path = file_path.rsplit('.', 1)[0] + '.wav'
    audio = AudioSegment.from_file(file_path)
    audio.export(wav_file_path, format="wav")
    return wav_file_path

def recognize_audio(file_path: str) -> str:
    """Use SpeechRecognition library to convert audio to text."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Recognition request error: {str(e)}")
