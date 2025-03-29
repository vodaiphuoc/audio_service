from test import add
from celery.result import AsyncResult
import asyncio

main_task = add.delay(10,10)


async def main():
    while True:
        result = AsyncResult(id= main_task.id)
        if result.ready():
            final_result = result.result
            print(final_result)

if __name__ == "__main__":
    asyncio.run(main())