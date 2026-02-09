from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import json
import uuid
import asyncio
from services.ai_orchestrator import AIOrchestrator
from services.video_generator import VideoGenerator
from models.schemas import VideoRequest, Scene, VideoPlan

app = FastAPI(title="Cinematic AI Agent API")

# CORS configuration for Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_orchestrator = AIOrchestrator()
video_generator = VideoGenerator()

@app.post("/api/generate-plan")
async def generate_video_plan(
    description: str = Form(...),
    mood: Optional[str] = Form("cinematic"),
    audio: Optional[UploadFile] = File(None)
):
    """Generate cinematic video plan"""
    
    # Save audio if provided
    audio_path = None
    if audio:
        audio_path = f"./temp/{uuid.uuid4()}.mp3"
        with open(audio_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
    
    # Generate plan
    plan = await ai_orchestrator.generate_cinematic_plan(
        description=description,
        mood=mood,
        audio_path=audio_path
    )
    
    return JSONResponse(content=plan.dict())

@app.post("/api/render-video")
async def render_video(request: VideoRequest):
    """Render video based on plan"""
    task_id = str(uuid.uuid4())
    
    # Start rendering in background
    asyncio.create_task(
        video_generator.render_video_task(task_id, request)
    )
    
    return {"task_id": task_id, "status": "processing"}

@app.get("/api/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Check video rendering status"""
    status = video_generator.get_task_status(task_id)
    return {"task_id": task_id, "status": status}

@app.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket for real-time progress updates"""
    await websocket.accept()
    try:
        while True:
            # Get progress from video generator
            progress = video_generator.get_progress(task_id)
            await websocket.send_json({"progress": progress})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

@app.get("/api/download-video/{task_id}")
async def download_video(task_id: str):
    """Download rendered video"""
    video_path = f"./output/{task_id}.mp4"
    return FileResponse(
        video_path,
        media_type='video/mp4',
        filename=f"cinematic_video_{task_id}.mp4"
    )
