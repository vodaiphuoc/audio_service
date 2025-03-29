import asyncio
from typing import Dict, List, Tuple, Union
import requests
import json
from loguru import logger
import threading

from .schemas.video_requests import MultiPartData
from database.object_storage.app import Firebase_Handler

class ConnectionManager:
    r"""
    Handling all current tasks of all active uses
    """
    def __init__(self, 
                 model_service_url:str, 
                 model_service_endpoint:str,
                 max_item:int = 20, 
        ):
        self.model_service_url = model_service_url
        self.model_service_endpoint = model_service_endpoint
        self.task_pool: asyncio.Queue = asyncio.Queue(maxsize= max_item)
        self._should_stop = asyncio.Event()

        self.object_storage = Firebase_Handler()

    async def add_user_task(self,
                            user_id:int, 
                            parse_data: List[MultiPartData]
        ):
        r"""
        Add user into `task_pool`. Call from router
        """
        await self.task_pool.put((user_id,parse_data))

    def _requests2model_service(
            self,
            file_data: List[MultiPartData]
        )->Dict[str, List[Dict[str,Union[float,str]]]]:
        r"""
        Make request to model service
        Args:
            file_data (List[MultiPartData]): request list file from 
            query use from queue
        
        Returns:
            a dictionary with key is request file name, value are list of segments of transcripts
        """
        data_per_file = {}
        with requests.post(
            url = f"{self.model_service_url}/{self.model_service_endpoint}", 
            files = [mltp.to_tuple for mltp in file_data],
            stream=True) as _response:

            for line in _response.iter_lines(decode_unicode=True, delimiter=b"\n"):
                if line:  # Ignore empty lines
                    try:
                        data = json.loads(line)

                        if data_per_file.get(data['file_name'], None) is not None:
                            data_per_file[data['file_name']].append(data['seg_dict'])
                        else:
                            data_per_file[data['file_name']] = []

                        logger.info("receive data")
                        # You can now work with the 'data' dictionary
                    except json.JSONDecodeError as e:
                        logger.info("JSONDecodeError for line: ", line)
                
        return data_per_file

    
    async def _pull_from_queue(
            self, 
            timeout: float = 1.0,
            batch_size:int = 2
        )->List[Tuple[int, List[MultiPartData]]]:
        r"""
        Pull out 5 requests from `task_queue`
        """
        items = []
        for _ in range(batch_size):
            try:
                item = await asyncio.wait_for(
                    self.task_pool.get(),
                    timeout=timeout / batch_size
                )
                items.append(item)
            except (asyncio.TimeoutError, asyncio.QueueEmpty) as err:
                break
            except Exception as e:
                break
        
        if len(items) > 0:
            return items
        else:
            return None

    async def background_loop(self):        
        while not self._should_stop.is_set():
            await asyncio.sleep(0.1)
            print(self.task_pool.qsize())
            batch = await self._pull_from_queue()
            if batch:
                logger.info("got batch")
                # flatten batch
                batch_multiparts = []
                # user_id2file_name = {}
                for user_id, multipart_list in batch:
                    assert isinstance(multipart_list, list)
                    batch_multiparts.extend(multipart_list)
                    # for multipart in multipart_list:
                    #     user_id2file_name[user_id].append(multipart.partdata.file_name)

                data_per_file = self._requests2model_service(file_data= batch_multiparts)
                with open("test_output.json","w") as fp:
                    json.dump(data_per_file,fp)

    def run_background_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.background_loop())
        finally:
            loop.close()

    def start_background(self):
        r"""
        Start background loop task, call from lifespan of app
        """
        global background_thread
        background_thread = threading.Thread(target=self.run_background_loop, daemon=True)
        background_thread.start()

    def shutdown_background(self):
        r"""
        Shutdown background loop task, call from lifespan of app
        """
        self._should_stop.set()
        print('shutting down')
