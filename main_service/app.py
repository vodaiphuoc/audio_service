from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uvicorn
import asyncio

from routers import video_router

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

# app.include_router(user_router)
app.include_router(video_router)

templates = Jinja2Templates(directory="main_service/templates")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})


async def main_run():
    config = uvicorn.Config("app:app",
    	port=8000, 
    	log_level="info", 
    	reload=True,
    	)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main_run())