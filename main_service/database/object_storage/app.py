import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import json
import os
import numpy as np
from typing import Union, Tuple, Literal
import uuid

from setting import SETTINGS

PROJECT_PATH = __file__.replace(os.path.join("main_service","database","object_storage","app.py"),"")

class Firebase_Handler(object):
    def __init__(self) -> None:
        self.app = self.init_app()
        assert self.app != False

    def init_app(self)->firebase_admin.App:
        cred = credentials.Certificate(os.path.join(PROJECT_PATH, 
                                                    SETTINGS.PATH2ACCOUNT_KEY, 
                                                    SETTINGS.ACCOUNT_KEY_FILE
        ))

        default_app = firebase_admin.initialize_app(cred, {
            'databaseURL': SETTINGS.DB_URL, 
            'storageBucket': SETTINGS.StorageBucketURL,
            'projectID': SETTINGS.PROJECT_ID
            })

        if isinstance(default_app, firebase_admin.App):
            return default_app
        else:
            return False

    def upload_video(
            self,
            user_id:int,
            randomzied_file_name: str,
            file_content: bytes
        )->None:

        bucket = storage.bucket(name = "bucket_"+str(user_id), app= self.app)
        # bucket = storage.bucket(name = "", app= self.app)

        _destination_path = os.path.join(randomzied_file_name.replace(".mp4",""),"video",randomzied_file_name)
        blob = bucket.blob(_destination_path)
        
        blob.upload_from_string(file_content)
        return None

