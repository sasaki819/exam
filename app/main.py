from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles # Added for static files
from app.routers import auth, questions, pages, summary # Import the new summary router

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(questions.router, prefix="/questions", tags=["questions"])
app.include_router(summary.router, prefix="/summary", tags=["summary"]) # Added summary router

# Include HTML page routers (should be last or have less specific paths)
app.include_router(pages.router, tags=["pages"])


# The root path "/" is now handled by pages.router
# If pages.router does not handle "/", you might want to add a root endpoint here
# or ensure one of the included routers does.
# For example, if pages.router handles "/" to serve exam.html, this is fine.
# If not, and you want a default API message:
# @app.get("/")
# async def root_api():
#     return {"message": "Welcome to the Quiz API. Navigate to /login or /exam for the web interface."}
# The current pages.router handles "/" to serve exam.html, so this explicit root is not needed.
