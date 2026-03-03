import warnings
# Filter annoying torchcodec warnings from pyannote
warnings.filterwarnings("ignore", module="pyannote.audio.core.io")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes

from app.database import engine, Base
from app.models import db_models

# Initialize FastAPI app
app = FastAPI(title="Meeting Assistant API")

# Create database tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router)

@app.get("/")
async def root():
    return {"message": "Meeting Assistant API is running 🚀"}
