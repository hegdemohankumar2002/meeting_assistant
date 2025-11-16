from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes

# Initialize FastAPI app
app = FastAPI(title="Meeting Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router)

@app.get("/")
async def root():
    return {"message": "Meeting Assistant API is running 🚀"}
