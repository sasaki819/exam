from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app import models # To use models.User
from app.routers.auth import get_current_user_or_none # For authentication

router = APIRouter()

# Ensure the templates directory is correctly identified relative to this file
# If pages.py is in app/routers/, then templates is ../../templates
# However, FastAPI's Jinja2Templates usually expects the path from where the app is run (e.g. project root)
# or an absolute path. For simplicity, assuming 'templates' is at the project root.
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def read_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/exam", response_class=HTMLResponse)
async def read_exam_page(request: Request):
    # The exam.js will handle token check and redirect to /login if not authenticated
    return templates.TemplateResponse("exam.html", {"request": request})

# Optional: Redirect root to /exam or /login
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Simple logic: if a token might exist, try exam, else login. JS will enforce.
    # This is just for convenience of accessing root.
    # A more robust way would involve actually checking token validity here if needed.
    return templates.TemplateResponse("exam.html", {"request": request, "title": "Exam"})
    # Or redirect: return RedirectResponse(url="/exam")
    # For now, let's serve exam.html, js will redirect to login if no token.
    # To be more explicit and avoid potential confusion, let's make root redirect to /login
    # from fastapi.responses import RedirectResponse
    # return RedirectResponse(url="/login", status_code=302)
    # For this task, serving exam.html at root is fine as per "or /" in requirement.
    # The JS on exam.html will redirect to /login if no token.
    # Let's make root explicitly serve login.html to be clearer.
    # Actually, the prompt says "exam.html (e.g. at /exam or /)". So serving exam.html at "/" is fine.
    # The JS in exam.html handles redirect if no token.
    return templates.TemplateResponse("exam.html", {"request": request})

@router.get("/summary", response_class=HTMLResponse)
async def read_summary_page(request: Request):
    # The summary.js will handle token check and redirect to /login if not authenticated
    return templates.TemplateResponse("summary.html", {"request": request})

@router.get("/manage-exam-types", response_class=HTMLResponse)
async def manage_exam_types_page(request: Request):
    # The manage_exam_types.js will handle token check and redirect to /login if not authenticated
    return templates.TemplateResponse("manage_exam_types.html", {"request": request})

@router.get("/manage-questions", response_class=HTMLResponse)
async def manage_questions_page(request: Request):
    # The manage_questions.js will handle token check for API calls 
    # and redirect to /login if not authenticated.
    return templates.TemplateResponse("manage_questions.html", {"request": request})
