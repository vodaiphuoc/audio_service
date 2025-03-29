# import json
# import os
# import whisper
# from typing import Generator,List
# from sqlalchemy.orm import Session
# from fastapi import HTTPException,status
# from fastapi import UploadFile

# from utils.video_utils import split_audio
# from schemas.video import TranscriptionHistoryItem

# from loguru import logger
# from pathlib import Path
# import uuid

# from moviepy.video.io.VideoFileClip import VideoFileClip
# import httpx
# import yt_dlp
# from typing import Union,Dict


# from ....setting import SETTINGS
# from models.models import TranscriptionHistory
# from services.model_service import transcribe_audio

# class TranscriptionService: 
#     def __init__(self, model_name: str = None):
#         self.model = whisper.load_model(model_name) if model_name else None
            
#     def transcribe_file(self, file_path: str) -> dict:
#         from services.model_service import app, transcribe_audio
        
#         with open(file_path, "rb") as f:
#             audio_data = f.read()
#         try:
#             # Sử dụng context manager để tạo phiên Modal tạm thời
#             with app.run():
#                 result = transcribe_audio.remote(audio_data, "medium")
#             print(result["segments"])
#             print('dang xu ly dung co afk')
#             return {
#                 "text": result["text"],
#                 "segments": result["segments"],
#             }   
#         except Exception as e:
#             logger.error(f"Transcription error with Modal: {e}")
#             # Fallback to local model
#             # if self.model is None:
#             #     self.model = whisper.load_model("medium")
#             # result = self.model.transcribe(file_path)
#             return {
#                 "text": "",
#                 "segments": "segments",
#             }
        
#     @classmethod
#     async def transcribe_and_save(cls, file: Union[UploadFile, str], db: Session, user_id: int):
#         from starlette.datastructures import UploadFile as StarletteUploadFile

#         # Tạo bản ghi với trạng thái processing = True
#         if isinstance(file, StarletteUploadFile):
#             original_extension = Path(file.filename).suffix
#             random_filename = f"{uuid.uuid4()}{original_extension}"
#             upload_dir = os.path.join(os.getcwd(), "uploads", "videos")
#             os.makedirs(upload_dir, exist_ok=True)

#             file_path = os.path.join(upload_dir, random_filename)
#             print(file_path)
#             with open(file_path, "wb") as f:
#                 f.write(file.file.read())
#         elif isinstance(file, str):
#             file_path = file  # Nếu file là string, nó đã là đường dẫn

#         # Tiếp tục xử lý như bình thường
#         file_size = os.path.getsize(file_path) / (1024 * 1024)
#         video = VideoFileClip(file_path)
#         video_duration = video.duration
#         video.close()

#         # Thực hiện transcribe
#         service = cls()
#         result = service.transcribe_file(file_path)
#         # Cập nhật bản ghi với kết quả
#         transcription = TranscriptionHistory(
#             user_id=user_id,
#             video_name=Path(file_path).name,
#             processing=False,
#             file_path=file_path,
#             file_size=file_size,
#             video_duration=video_duration,
#             text=result["text"],
#             segment=json.dumps(result["segments"])
#         )
#         db.add(transcription)
#         db.commit()

#         return result["segments"], result["text"]

#     @staticmethod
#     def get_user_history(db: Session, user_id: int) -> List[TranscriptionHistoryItem]:
#         histories = db.query(TranscriptionHistory).filter(TranscriptionHistory.user_id == user_id).all()
#         return [TranscriptionHistoryItem.from_orm(h) for h in histories]
    
#     @staticmethod
#     def delete_transcription_history(db: Session, history_id: int, user_id: int):
#         # Tìm bản ghi lịch sử
#         history = db.query(TranscriptionHistory).filter(
#             TranscriptionHistory.id == history_id,
#             TranscriptionHistory.user_id == user_id
#         ).first()

#         if history:
#             if os.path.exists(history.file_path):
#                 os.remove(history.file_path)
#         if not history:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Transcription history not found or access denied"
#             )

#         # Xóa bản ghi  
#         db.delete(history)
#         db.commit()
#         return {"message": "Transcription history deleted successfully"}
    
#     @staticmethod
#     async def generate_gemini_content(prompt_text: str) -> Dict:
#         try:
#             gemini_api_key = SETTINGS.GEMINI_API_KEY
#             url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            
#             headers = {
#                 "Content-Type": "application/json"
#             }
            
#             payload = {
#                 "contents": [{
#                     "parts": [{
#                         "text": prompt_text
#                     }]
#                 }]
#             }
            
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 response = await client.post(url, headers=headers, json=payload)
#                 response.raise_for_status()  # Kiểm tra nếu request bị lỗi
                
#                 data = response.json()

#                 # Log response để debug
#                 logger.debug(f"Gemini API response: {data}")

#                 return data

#         except httpx.HTTPStatusError as e:
#             logger.error(f"HTTP error occurred: {e.response.text if e.response else str(e)}")
#             raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

#         except Exception as e:
#             logger.error(f"Gemini API call failed: {str(e)}")
#             raise HTTPException(status_code=500, detail="Failed to fetch response from Gemini API")
    
    
#     @staticmethod
#     async def download_video(url: str) -> str:
#         try:
#             output_dir = "downloads"
#             os.makedirs(output_dir, exist_ok=True)
#             filename = f"{uuid.uuid4()}.mp4"
#             output_path = os.path.join(output_dir, filename)

#             ydl_opts = {
#                 'format': 'best',
#                 'outtmpl': output_path,
#                 'quiet': True,
#                 'noplaylist': True,
#             }

#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 ydl.download([url])

#             return output_path

#         except Exception as e:
#             raise Exception(f"Failed to download video: {str(e)}")
