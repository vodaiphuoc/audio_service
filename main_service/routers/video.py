import json
import os
from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    APIRouter, 
    HTTPException, 
    Response,
    Depends,
    status,
    Request,
    UploadFile
)
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

# from dependencies import get_current_user_id 
from loguru import logger
from typing import List,Union
import asyncio

# from database.sql.orm_model import TranscriptionHistory
# from database.sql.db import get_db
# from video_utils.video_service import TranscriptionService

from .video_router_components.task_queue import ConnectionManager
from .video_router_components.schemas.video_requests import MultiPartData, PartData
from .video_router_components.schemas.video import TranscriptionHistoryItem, GeminiRequest, VideoRequest

from setting import SETTINGS

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.manager = ConnectionManager(
        model_service_url = "http://"+SETTINGS.DEPLOY_DOMAIN, 
        model_service_endpoint = SETTINGS.ENDPOINT_ROUTER
    )
    app.manager.start_background()
    yield
    await app.manager.shutdown_background()


video_router = APIRouter(lifespan = lifespan)


@video_router.post("/uploads")
async def transcribe_file(
        videoInputs: List[UploadFile],
        request: Request,
        # db: Session = Depends(get_db), 
        user_id: int  = 1 #= Depends(get_current_user_id)
    ):
    r"""
    Main router for `video_router`.
    The workflow includes:
        - handling user upload files (the User can upload one 
            or more files per one post request)
        - add data into SQLAlchemy (relation db)
        - add files into Firebase (object storage)
        - add files, client id into task_queue. The queue
            is handled by `update_status` router (make request
            to `model_service`, do translation) as background tasks
        - return status to UI immediately (no waiting for transcript files)
    """
    _parse_data = []
    for _ith, _file in enumerate(videoInputs):
        content = await _file.read()
        
        _parse_data.append(MultiPartData(
            key= "files",
            partdata = PartData(
                file_name = _file.filename, 
                content = content, 
                content_type = _file.content_type)
            )
        )
        request.app.manager.object_storage.upload_video(
            user_id = user_id,
            randomzied_file_name = _file.filename,
            file_content = content
        )

    await request.app.manager.add_user_task(user_id, _parse_data)
    # segments, text = await TranscriptionService.transcribe_and_save(file, db, user_id=user_id)
    return JSONResponse(content= {"message": "Successfully upload videos"})


@video_router.get("/stream_status")
async def update_status(request: Request):
    r"""
    A router for connecting with Client JS through server side event.
    Do the following task:
        - run while True loop in another thread
        - pull out element from `task_queue`, make request to `model_service`
        - with result from `model_service`, update database (both SQL and Object storage)
        - yield reponse to UI status of making transcript
    """
    async def event_stream():
        while True:
            try:
                if await request.is_disconnected():
                    break
                
                await asyncio.sleep(0.1)
                yield 'data: {}\n\n'.format("not get batch")

            except (asyncio.CancelledError, KeyboardInterrupt):
                break
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")



# @video_router.delete(
#         "/transcribe/history/{history_id}", 
#         status_code=status.HTTP_204_NO_CONTENT)
# async def delete_transcription_history(
#         history_id: int, 
#         db: Session = Depends(get_db), 
#         user_id: int = Depends(get_current_user_id)
#     ):
#     print(f"Deleting history_id: {history_id} for user_id: {user_id}")
#     # Gọi service để xóa lịch sử
#     return TranscriptionService.delete_transcription_history(db=db, history_id=history_id, user_id=user_id)

# @video_router.get(
#         "/transcription_histories", 
#         response_model=List[TranscriptionHistoryItem])
# def get_transcription_histories(
#         db: Session = Depends(get_db),
#         user_id: int = Depends(get_current_user_id)
#     ):
#     histories = TranscriptionService.get_user_history(db, user_id)
#     return histories

# @video_router.get("/video/{video_id}")
# async def get_video(
#         video_id: str, 
#         db: Session = Depends(get_db), 
#         user_id: int = Depends(get_current_user_id)
#     ):
#     video = db.query(TranscriptionHistory).filter(  # Dùng TranscriptionHistory model
#         TranscriptionHistory.id == video_id,
#         TranscriptionHistory.user_id == user_id
#     ).first()

#     if not video:
#         raise HTTPException(status_code=404, detail="Video not found")
       
#     return FileResponse(
#         video.file_path,
#         media_type="video/mp4",
#         filename=video.video_name
#     )

# @video_router.delete(
#         "/transcribe/history/{history_id}", 
#         status_code=status.HTTP_204_NO_CONTENT)
# async def delete_transcription_history(
#         history_id: int, 
#         db: Session = Depends(get_db), 
#         user_id: int = Depends(get_current_user_id)
#     ):
#     # Find the history entry
#     history = db.query(TranscriptionHistory).filter(
#         TranscriptionHistory.id == history_id,
#         TranscriptionHistory.user_id == user_id
#     ).first()
    
#     if not history:
#         raise HTTPException(status_code=404, detail="History not found")
    
#     try:
#         # Delete the video file if it exists
#         if history.file_path and os.path.exists(history.file_path):
#             os.remove(history.file_path)
        
#         # Delete from database
#         db.delete(history)
#         db.commit()
        
#         return Response(status_code=status.HTTP_204_NO_CONTENT)
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error deleting transcription history: {str(e)}"
#         )

# @video_router.get("/transcribe/history/{history_id}")
# async def get_transcription_history(
#         history_id: int,
#         db: Session = Depends(get_db),
#         user_id: int = Depends(get_current_user_id)
#     ):
#     history = db.query(TranscriptionHistory).filter(
#         TranscriptionHistory.id == history_id,
#         TranscriptionHistory.user_id == user_id
#     ).first()
    
#     if not history:
#         raise HTTPException(status_code=404, detail="History not found")
    
#     return {
#         "id": history.id,
#         "text": history.text,           
#         "video_duration": history.video_duration,
#         "segment": history.segment  # Thêm trường segment vào response
#     }

# @video_router.post("/generate_gemini_content")
# async def generate_gemini_content(req: GeminiRequest):
#     try:
#         # Tạo prompt yêu cầu Gemini dịch
#         prompt = f"""Translate the following text into {req.language}.
#         ONLY return the translated text, no explanation, no commentary, no additional analysis.

#         Text to translate:
#         {req.text}"""

#         # Gọi Gemini API
#         data = await TranscriptionService.generate_gemini_content(prompt)

#         # Parse response từ Gemini
#         if "candidates" in data and data["candidates"]:
#             content = data["candidates"][0].get("content", {})
#             if "parts" in content and content["parts"]:
#                 translated_text = content["parts"][0].get("text", "")
#                 return {"translated_text": translated_text}
        
#         raise HTTPException(status_code=500, detail="Invalid response format from Gemini")
    
#     except Exception as e:
#         logger.error(f"Error generating Gemini content: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @video_router.post("/transcribe_and_download")
# async def transcribe_file(
#         request: VideoRequest, 
#         db: Session = Depends(get_db), 
#         user_id: int = Depends(get_current_user_id)
#     ):
#     print(f"User ID: {user_id}")  # Debug xem user_id có nhận đúng không
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Unauthorized")

#     # Lấy URL từ request JSON
#     video_url = request.url
#     video_path = await TranscriptionService.download_video(video_url)
#     print(video_path)
#     # Gọi hàm async với await
#     await TranscriptionService.transcribe_and_save(video_path, db, user_id=user_id)

#     return {"status": "done"}

# Updated endpoint with more debugging and error handling
# from translate import Translator

# @video_router.post("/translate_text")
# async def translate_text(
#     req: GeminiRequest,
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_current_user_id)
# ):
#     try:
#         logger.info(f"Translation request: language={req.language}, history_id={req.history_id}")
        
#         # If history_id is provided, translate segments
#         if req.history_id:
#             history = db.query(TranscriptionHistory).filter(
#                 TranscriptionHistory.id == req.history_id,
#                 TranscriptionHistory.user_id == user_id
#             ).first()
            
#             if not history:
#                 logger.error(f"History not found: {req.history_id}")
#                 raise HTTPException(status_code=404, detail="History not found")
            
#             # Parse the segments
#             segments = []
#             try:
#                 segments = json.loads(history.segment)
#                 logger.info(f"Loaded {len(segments)} segments for translation")
#             except Exception as e:
#                 logger.error(f"Error parsing segments: {str(e)}")
#                 raise HTTPException(status_code=500, detail=f"Error parsing segments: {str(e)}")
            
#             # Check if the translate library can handle this language
#             try:
#                 # Initialize translator with target language
#                 translator = Translator(to_lang=req.language)
                
#                 # Test translation with a short string
#                 test_translation = translator.translate("Hello")
#                 logger.info(f"Test translation successful: 'Hello' -> '{test_translation}'")
#             except Exception as e:
#                 logger.error(f"Error initializing translator: {str(e)}")
#                 raise HTTPException(
#                     status_code=400, 
#                     detail=f"Translation to language '{req.language}' is not supported or error occurred: {str(e)}"
#                 )
            
#             # Translate each segment with proper error handling
#             translated_segments = []
#             for i, segment in enumerate(segments):
#                 try:
#                     if i < 3:  # Log just a few segments for debugging
#                         logger.info(f"Translating segment {i}: '{segment['text'][:30]}...'")
                    
#                     # This is synchronous and simpler
#                     translated_text = translator.translate(segment['text'])
                    
#                     if i < 3:  # Log just a few translations for debugging
#                         logger.info(f"Translated segment {i}: '{translated_text[:30]}...'")
                    
#                     new_segment = segment.copy()
#                     new_segment["text"] = translated_text
#                     translated_segments.append(new_segment)
#                 except Exception as e:
#                     logger.error(f"Error translating segment {i}: {str(e)}")
#                     # If translation fails, keep original text
#                     translated_segments.append(segment.copy())
            
#             logger.info(f"Successfully translated {len(translated_segments)} segments")
            
#             # Translate full text if provided
#             translated_text = ""
#             if req.text:
#                 try:
#                     logger.info(f"Translating main text: '{req.text[:50]}...'")
#                     translated_text = translator.translate(req.text)
#                     logger.info(f"Translated main text: '{translated_text[:50]}...'")
#                 except Exception as e:
#                     logger.error(f"Error translating main text: {str(e)}")
#                     translated_text = req.text  # Fallback to original
            
#             return {
#                 "translated_text": translated_text,
#                 "translated_segments": translated_segments
#             }
        
#         # If only text translation is requested
#         elif req.text:
#             try:
#                 translator = Translator(to_lang=req.language)
#                 translated_text = translator.translate(req.text)
#                 return {"translated_text": translated_text}
#             except Exception as e:
#                 logger.error(f"Error translating text: {str(e)}")
#                 raise HTTPException(
#                     status_code=500, 
#                     detail=f"Translation failed: {str(e)}"
#                 )
        
#         else:
#             raise HTTPException(status_code=400, detail="No text or history_id provided")
    
#     except HTTPException:
#         # Re-raise HTTP exceptions as is
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error in translation: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")