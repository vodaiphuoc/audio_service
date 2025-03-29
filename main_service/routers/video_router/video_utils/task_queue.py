import asyncio
from typing import Dict, List, Tuple, Union

class ConnectionManager:
    r"""
    Handling all current tasks of all active uses
    """
    def __init__(self, max_item_per_client:int = 40):
        self.max_item_per_client = max_item_per_client
        self.task_pool: Dict[int, asyncio.Queue] = {}

    async def add_user_task(self, 
                            user_id:int, 
                            parse_data: List[Tuple[Union[str, Tuple[Union[str, bytes]]]]]
        ):
        if user_id not in list(self.task_pool.keys()):
            self.task_pool[user_id] = asyncio.Queue(maxsize = self.max_item_per_client)
        
        await self.task_pool[user_id].put((parse_data, user_id))

    async def get_item_by_user(self, user_id:int):
        r"""
        Get one item from task queue of selected user

        Returns:
            a tuple of `user_id` and `parse_data`
        """
        return await self.task_pool[user_id].get()
