import asyncio
import queue
import os

from fastapi import FastAPI

from autoredir import usbip_autoredir
from autoredir import usbip_action


app = FastAPI()
redir_queue = queue.Queue()


@app.on_event("startup")
async def app_startup():
    filter_rules_path = os.environ.get("FILTER_RULES_PATH")
    servers_file_path = os.environ.get("SERVERS_FILE_PATH")

    asyncio.create_task(usbip_autoredir.usbip_autoredir(
        usbip_action.UsbipActionAttach(servers_file_path, redir_queue),
        filter_rules_path,
    ))


@app.get("/")
async def root():
    redir_queue.put("Ole ole")
    return {"message": "Hello World"}
