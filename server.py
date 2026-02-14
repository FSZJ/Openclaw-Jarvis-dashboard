"""
OpenClaw Dashboard - Main FastAPI Server
"""
import asyncio
from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from config import SERVER_HOST, SERVER_PORT
from api.auth import router as auth_router
from api.status import router as status_router
from api.dashboard import router as dashboard_router
from api.agents import router as agents_router
from api.channels import router as channels_router
from api.actions import router as actions_router
from api.todos import router as todos_router
from api.integrations import router as integrations_router
from api.usage import router as usage_router
from services.auth import AuthService
from services.collector import StatusCollector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"OpenClaw Dashboard starting on {SERVER_HOST}:{SERVER_PORT}")
    yield
    # Shutdown
    print("OpenClaw Dashboard shutting down")


# Create FastAPI application
app = FastAPI(
    title="OpenClaw Dashboard",
    description="Visual dashboard for OpenClaw system monitoring and management",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(status_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(channels_router, prefix="/api")
app.include_router(actions_router, prefix="/api")
app.include_router(todos_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(usage_router, prefix="/api")

# Frontend path - serve built Vue app
FRONTEND_PATH = Path(__file__).parent / "frontend" / "dist"

# Mount static files
if FRONTEND_PATH.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_PATH / "assets")), name="assets")


@app.get("/")
async def root():
    """Serve the main dashboard page"""
    if FRONTEND_PATH.exists():
        return FileResponse(str(FRONTEND_PATH / "index.html"))
    else:
        return {
            "message": "OpenClaw Dashboard API",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "auth": "/api/auth",
                "status": "/api/status",
                "agents": "/api/agents",
                "channels": "/api/channels",
                "actions": "/api/actions"
            }
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.websocket("/ws")
async def ws_status(websocket: WebSocket):
    """WebSocket push channel for dashboard live status."""
    token = websocket.query_params.get("token")
    auth_service = AuthService()
    if not token or not auth_service.verify_token(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    collector = StatusCollector()

    try:
        while True:
            payload = collector.get_full_status(light=True)
            await websocket.send_json({
                "type": "status_update",
                "payload": payload
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
