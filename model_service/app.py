# from pydantic
import os
import modal
from pathlib import Path
from schemas import RequestBodyData, ModelResult
import asyncio
from uuid import uuid4
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from typing import List

app_image = modal.Image.debian_slim().pip_install(
    "fastapi[standard]==0.115.8",
    "openai-whisper",
    "torch",
    "ffmpeg-python"
).apt_install("ffmpeg")

whisper_cache = modal.Volume.from_name("whisper-cache", create_if_missing=True)
CACHE_PATH = "/root/.cache/whisper"

app = modal.App("whisper-compile-service")

@app.cls(
    image=app_image,
    gpu="T4",
    scaledown_window = 7,
    volumes={CACHE_PATH: whisper_cache},
)
class ModelInference(object):
    @modal.enter()
    def enter(self):
        r"""
        Method replaces for __init__ in normal class, only run onence
        when `modal`'s container is created
        """
        import whisper
        import torch

        self.model = whisper.load_model("base")
        self.model.eval()
        self.model.forward = torch.compile(self.model.forward,
            mode = "reduce-overhead",
            fullgraph = True,
            dynamic = True
        )

    @modal.method()
    def inference(self, cached_local_path:str, file_name:str)->ModelResult:
        result = self.model.transcribe(cached_local_path)
        return ModelResult(file_name = file_name, **result)

    @modal.fastapi_endpoint(method="POST", docs=True)
    async def router(self, files: List[UploadFile]):
        
        _kwarg_list = []
        for _file_req in files:
            _temp_file_name = f'temp_write_{_file_req.filename}_'+ str(uuid4())+'.mp4'

            content = await _file_req.read()
            with open(_temp_file_name, 'wb') as fp:
                fp.write(content)

            _kwarg_list.append({
                'cached_local_path': _temp_file_name,
                "file_name": _file_req.filename
            })

        tasks = [
            asyncio.create_task(self.inference.local(**_kwargs))
            for _kwargs in _kwarg_list
        ]

        master_results = await asyncio.gather(*tasks)
        return JSONResponse(master_results)
