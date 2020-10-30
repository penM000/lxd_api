import asyncio
import datetime
import json
import random
import string
#import aiofiles


from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, Response, Response
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

import items

# fastapi
app = FastAPI()

#app.mount("/html", StaticFiles(directory="html"), name="root")


@app.get("/get_all_machine")
async def request_all_machine_name():
    return items.get_all_machine_name()


@app.get("/launch_machine")
async def request_launch_machine(
    hostname: str,
    imagealias="",
    imagefinger="",
    machinetype="container",
    cpu=2,
    memory="2GB",
    storage="32GB",
    srcport=8080,
    startcheck=1,
    https=0,
    httpstatus=200,
    starttimeout=60,
    startportassign=10000
):

    result = await items.launch_machine(
        hostname,
        imagealias,
        imagefinger,
        machinetype,
        cpu,
        memory,
        storage,
        srcport,
        startcheck,
        https,
        httpstatus,
        starttimeout,
        startportassign
    )
    return result


@app.get("/start")
async def request_launch_container_machine(name: str):
    return items.start_machine(name)


@app.get("/stop")
async def request_launch_container_machine(name: str):
    return items.stop_machine(name)
