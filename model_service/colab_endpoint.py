import os
import modal
from pathlib import Path
import asyncio
from uuid import uuid4
from fastapi import UploadFile, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


from pydantic import BaseModel
from typing import List, Dict, Union
from dotenv import load_dotenv
from loguru import logger
import uvicorn
from contextlib import asynccontextmanager
import ngrok

import asyncio


from faster_whisper import WhisperModel, BatchedInferencePipeline
import torch

load_dotenv() 

# class ModelResult(BaseModel):
#     r"""
#     Output of whisper model for each file
#     """
#     file_name: str
#     text: str
#     segments: List[Dict[str, Union[float, str, List[int]]]]
#     language:str

class ModelInference(object):
    def __init__(self):
        single_model = WhisperModel("base", device="cuda", compute_type="int8_float16")
        self.model = BatchedInferencePipeline(model=single_model)

    def forward(self, cached_local_path:str, file_name:str):
        result = self.model.transcribe(cached_local_path)
        return result



NGROK_AUTH_TOKEN = os.environ['NGROK_AUTH_TOKEN']
APPLICATION_PORT = os.environ['APPLICATION_PORT']
HTTPS_SERVER = os.environ['HTTPS_SERVER']
DEPLOY_DOMAIN = os.environ['DEPLOY_DOMAIN']


origins = [
    "http://mullet-immortal-labrador.ngrok-free.app/",
    "https://mullet-immortal-labrador.ngrok-free.app/",
    "http://localhost",
    "http://localhost:8080/",
    "http://localhost:8000/",
    "http://127.0.0.1:8000/",
    "http://127.0.0.1:8000"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    proto: "http", "tcp", "tls", "labeled"
    """
    app.model = ModelInference()
    logger.info("Setting up Ngrok Tunnel")
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    ngrok.forward(addr = HTTPS_SERVER+':'+str(APPLICATION_PORT),
                  proto = "http",
                  domain = DEPLOY_DOMAIN
                  )
    
    yield
    logger.info("Tearing Down Ngrok Tunnel")
    ngrok.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware, 
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"]
                   )

@app.post(path= "/",response_class=JSONResponse)
async def inference(files: List[UploadFile], request: Request):
        
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
            asyncio.create_task(request.app.model.forward(**_kwargs))
            for _kwargs in _kwarg_list
        ]

        master_results = await asyncio.gather(*tasks)
        return JSONResponse(master_results)


async def main():
    config = uvicorn.Config("colab_endpoint:app",
                            host=HTTPS_SERVER,
                            port=int(APPLICATION_PORT),
                            reload=True,
                            log_level="info",
                            )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())

    