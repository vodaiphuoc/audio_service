from dataclasses import dataclass
from typing import Literal, Tuple, Union


@dataclass
class PartData:
    file_name: str
    content: Union[str, bytes]
    content_type: str

@dataclass
class MultiPartData:
    key: Literal["files"]
    partdata: PartData

    @property
    def to_tuple(self)->Tuple:
        return (self.key,
                (self.partdata.file_name, 
                 self.partdata.content, 
                 self.partdata.content_type)
        )
