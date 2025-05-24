# app/main.py
from fastapi import FastAPI
from app.routers import questions, auth, summary, pages # Existing routers
from app.routers import exam_types # New router
from app.db import database, init_db
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # If you have CORS middleware

# Create database tables if they don't exist (e.g., on first run)
# In a production app with Alembic, you might handle this differently.
# models.Base.metadata.create_all(bind=database.engine) # init_db.init_db() might handle this

app = FastAPI(title="Quiz App")

# Optional: CORS Middleware (if you have it, ensure it's configured correctly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(pages.router, tags=["Pages"]) # Serve HTML pages
app.include_router(questions.router, prefix="/questions", tags=["Questions"])
app.include_router(summary.router, prefix="/summary", tags=["Summary"])
app.include_router(exam_types.router) # Add the new exam_types router

# Optional: Initialize DB with some data (if init_db.py is used)
# @app.on_event("startup")
# def on_startup():
#     init_db.init_db() # Call your init_db function if needed
