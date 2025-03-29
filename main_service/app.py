from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from routers import user_router, video_router

app = FastAPI()

# uploads_directory = os.path.join(os.path.dirname(__file__), "uploads")
# app.mount("/uploads", StaticFiles(directory=uploads_directory), name="uploads")

static_directory = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_directory), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(video_router)

templates = Jinja2Templates(directory="templates")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("authentication.html", {"request": request})
