import asyncio
import os
import cv2
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel

load_dotenv()


from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from core.vision_engine import VisionEngine
from core.audio_engine import AudioEngine
from core.threat_engine import ThreatEngine

app = FastAPI(title="SurveilX Multi-Modal Security System", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
vision_engine = VisionEngine()
audio_engine = AudioEngine()
threat_engine = ThreatEngine(vision_engine, audio_engine)
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(vision_engine.start_processing())
    asyncio.create_task(audio_engine.start_processing())
    asyncio.create_task(threat_engine.monitor_threats())
@app.on_event("shutdown")
async def shutdown_event():
    vision_engine.stop()
    audio_engine.stop()
    threat_engine.stop()
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
@app.get("/video_feed")
async def video_feed():
    async def generate_frames():
        while True:
            frame_bytes = await vision_engine.get_latest_frame_bytes()
            if frame_bytes is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                await asyncio.sleep(0.03)
            else:
                await asyncio.sleep(0.03)
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
@app.get("/api/status")
async def get_status():
    return {
        "threat_level": threat_engine.current_threat_level,
        "active_alerts": threat_engine.active_alerts,
        "tampering": vision_engine.tampering_status
        }

class ScenarioRequest(BaseModel):
    scenario: str

@app.post("/api/set_scenario")
async def set_scenario(req: ScenarioRequest):
    if req.scenario == "threat":
        vision_engine.set_source("threat.mp4")
        audio_engine.set_source("threat.wav")
    elif req.scenario == "webcam":
        vision_engine.set_source(0)
        audio_engine.set_source("normal.wav")
    else:
        vision_engine.set_source("normal.mp4")
        audio_engine.set_source("normal.wav")
    
    # Reset threat engine alerts so UI is fresh
    threat_engine.current_threat_level = "Normal"
    threat_engine.active_alerts = []
    
    return {"status": "success", "scenario": req.scenario}

@app.post("/api/upload_scenario")
async def upload_scenario(file: UploadFile = File(...)):
    video_path = "uploaded_scenario.mp4"
    audio_path = "uploaded_scenario.wav"
    
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        try:
            from moviepy import VideoFileClip
        except ImportError:
            from moviepy.editor import VideoFileClip
        video = VideoFileClip(video_path)
        if video.audio is not None:
            video.audio.write_audiofile(audio_path, codec='pcm_s16le', fps=16000, logger=None)
        video.close()
    except Exception as e:
        print(f"Error extracting audio: {e}")
        
    vision_engine.set_source(video_path)
    audio_engine.set_source(audio_path)
    
    threat_engine.current_threat_level = "Normal"
    threat_engine.active_alerts = []
    
    return {"status": "success", "message": "Scenario uploaded successfully"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "SurveilX"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
