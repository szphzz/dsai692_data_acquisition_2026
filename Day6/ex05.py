import asyncio
import time
import httpx
from fastapi import FastAPI

app = FastAPI()

url = "https://httpbin.org/delay/1.2"  # send a response after 1.2 sec


@app.get("/sync")
def sync_call():
    response1 = httpx.get(url)
    response2 = httpx.get(url)
    return {"first": response1.json(),
            "second": response2.json()}


@app.get("/async")
async def async_call():
    async with httpx.AsyncClient() as client:
            task1 = client.get(url)
            task2 = client.get(url)
            response1, response2 = await asyncio.gather(task1, task2)
    return {"first": response1.json(),
            "second": response2.json()}
