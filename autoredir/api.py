from typing import List
import asyncio
import queue
import os

from fastapi import FastAPI, HTTPException, status

from autoredir import usbip_autoredir
from autoredir import usbip_action
from autoredir.models import ServerCreate, ServerShow, UsbFilterRule


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


@app.post("/create-server")
def create_server(server: ServerCreate) -> ServerShow:
    return ServerShow(
        name=server.name,
        address=server.address,
        available=False,
        rules=[],
        devs=[]
    )


@app.put("/update-common-rules")
def update_server_rules(rules: List[UsbFilterRule]):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Error",
    )


@app.put("/update-server-rules/{server_name}")
def update_server_rules(server_name: str, rules: List[UsbFilterRule]):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Server with name {server_name} does not exist",
    )


@app.delete("/remove-server/{name}")
def remove_server(server_name: str):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Server with name {server_name} does not exist",
    )


@app.get("/all")
def get_servers() -> List[ServerShow]:
    return []


@app.post("/attach/{server_name}/{dev_busid}")
def attach_dev(server_name: str, dev_busid: str):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Server with name {server_name} does not exist",
    )


@app.delete("/detach/{server_name}/{dev_busid}")
def detach_dev(server_name: str, dev_busid: str):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Server with name {server_name} does not exist",
    )
