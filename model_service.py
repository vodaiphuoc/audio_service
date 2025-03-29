import os
import modal
from pathlib import Path

app_image = modal.Image.debian_slim().pip_install(
    "openai-whisper",
    "torch",
    "ffmpeg-python"
).apt_install("ffmpeg")

whisper_cache = modal.Volume.from_name("whisper-cache", create_if_missing=True)
CACHE_PATH = "/root/.cache/whisper"

app = modal.App("whisper-service")

@app.function(
    image=app_image,
    volumes={CACHE_PATH: whisper_cache},
    gpu="T4"
)
def transcribe_audio(audio_data, model_name="medium", file_extension=".mp3"):
    """Transcribe audio with optimal settings for GPU T4"""
    import whisper
    import torch
    
    # Kiểm tra GPU
    is_gpu_available = torch.cuda.is_available()
    gpu_info = f"GPU: {torch.cuda.get_device_name(0)}" if is_gpu_available else "Không có GPU"
    print(f"Trạng thái GPU: {is_gpu_available} - {gpu_info}")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Lưu file tạm
    temp_path = f"/tmp/audio_input{file_extension}"
    with open(temp_path, "wb") as f:
        f.write(audio_data)
    
    print(f"Đang tải model {model_name}...")
    model = whisper.load_model(model_name, device=device)
    
    # Transcribe - tự động phát hiện ngôn ngữ
    print("Đang transcribe...")
    result = model.transcribe(
        temp_path, 
        verbose=True     # In chi tiết quá trình
    )
    
    # Thêm thông tin để debug
    detected_language = result.get("language", "unknown")
    print(f"Đã phát hiện ngôn ngữ: {detected_language}")
    
    # Thêm thông tin GPU vào kết quả
    result["gpu_used"] = is_gpu_available
    result["gpu_info"] = gpu_info
    
    return result
