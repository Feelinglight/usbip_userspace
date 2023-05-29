from typing import List, Optional
import asyncio
import queue
import os

from fastapi import FastAPI, HTTPException, status

from autoredir import usbip_autoredir
from autoredir import usbip_action
from autoredir.servers_manager import ServersManager
from autoredir.models import ServerCreate, ServerShow, UsbFilterRule


app = FastAPI()
redir_queue = queue.Queue()
servers_manager: Optional[ServersManager] = None


@app.on_event("startup")
async def app_startup():
    filter_rules_path = os.environ.get("FILTER_RULES_PATH")
    servers_file_path = os.environ.get("SERVERS_FILE_PATH")
    usbip_attach_action = usbip_action.UsbipActionAttach(servers_file_path, redir_queue)

    global servers_manager
    servers_manager = ServersManager(usbip_attach_action)

    asyncio.create_task(usbip_autoredir.usbip_autoredir(
        usbip_attach_action,
        filter_rules_path,
    ))


@app.post("/create-server")
def create_server(server: ServerCreate):
    res, msg = servers_manager.add_server(server)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )


@app.put("/update-common-rules")
def update_server_rules(rules: List[UsbFilterRule]):
    servers_manager.set_server_filters(None, rules)


@app.put("/update-server-rules/{server_name}")
def update_server_rules(server_name: str, rules: List[UsbFilterRule]):
    servers_manager.set_server_filters(server_name, rules)


@app.delete("/remove-server/{server_name}")
def remove_server(server_name: str):
    res, msg = servers_manager.remove_server(server_name)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )


@app.get("/all")
def get_servers() -> List[ServerShow]:
    return []


@app.post("/attach/{server_name}/{dev_busid}")
def attach_dev(server_name: str, dev_busid: str):
    res, msg = servers_manager.attach_device(server_name, dev_busid)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )


@app.delete("/detach/{server_name}/{dev_busid}")
def detach_dev(server_name: str, dev_busid: str):
    res, msg = servers_manager.detach_device(server_name, dev_busid)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )
