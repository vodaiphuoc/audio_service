import os
import modal
from pathlib import Path
import asyncio
from uuid import uuid4
from fastapi import UploadFile, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware


from pydantic import BaseModel
from typing import List, Dict, Union, Generator
from dotenv import load_dotenv
from loguru import logger
import uvicorn
from contextlib import asynccontextmanager
import ngrok
import dataclasses
import json
import itertools

from faster_whisper import WhisperModel, BatchedInferencePipeline
import torch

load_dotenv() 


class ModelInference(object):
    r"""
    Main class for serving model
    with whisper model got from `faster_whisper`
    REF: https://github.com/SYSTRAN/faster-whisper/tree/master
    """
    def __init__(self):
        single_model = WhisperModel(
            "base", 
            device="cuda" if torch.cuda.is_available() else "cpu", 
            compute_type="int8_float16" if torch.cuda.is_available() else "int8",
            download_root=".checkpoints"
        )
        self.model = BatchedInferencePipeline(model=single_model)

    async def forward(self, cached_local_path:str)->Generator:
        segments, info = self.model.transcribe(cached_local_path)
        return segments


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

def generator_wrapper(
        file_generator: Generator, 
        file_kwargs: Dict[str,str]
        ):
    r"""
    A wrapper of output generator with its corresponding file name
    """
    for ele in file_generator:
        yield json.dumps({
                'file_name': file_kwargs['file_name'],
                "seg_dict": {
                    "start": ele.start,
                    "end": ele.end,
                    "text": ele.text
                }
            }).encode() + b"\n"

async def streaming_segements_result(
        master_results: List[Generator], 
        _kwarg_list: List[Dict[str,str]]
    ):
    r"""
    Main generator for returning data to main service
    Merge all generators of all requests files into one generator
    """
    gen_warpper_list = [generator_wrapper(
        file_generator = seg_generator, 
        file_kwargs = kwarg_dict
        ) for seg_generator, kwarg_dict 
        in zip(master_results, _kwarg_list)
    ]

    for ele in  itertools.chain(*gen_warpper_list):
        yield ele
    
    logger.info('done yielding ...')

@app.post(path= "/",response_class=StreamingResponse)
async def inference(files: List[UploadFile], request: Request):
        print('receive files')
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
            request.app.model.forward(_kwargs['cached_local_path'])
            for _kwargs in _kwarg_list
        ]
        
        master_results = await asyncio.gather(*tasks)
        
        return StreamingResponse(
            content= streaming_segements_result(master_results,_kwarg_list), 
            media_type="application/x-ndjson"
        )


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

    