from pydantic import BaseModel
from typing import List, Dict, Union

class ModelResult(BaseModel):
    r"""
    Output of whisper model for each file
    """
    file_name: str
    text: str
    segments: List[Dict[str, Union[float, str, List[int]]]]
    language:str

