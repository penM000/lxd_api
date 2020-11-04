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
async def request_start_machine(hostname: str):
    return items.start_machine(hostname)


@app.get("/stop")
async def request_stop_machine(hostname: str):
    return items.stop_machine(hostname)


@app.get("/exec_command")
async def request_exec_command_machine(hostname: str, command: str):
    return await items.exec_command_to_machine(hostname, command)


@app.post("/uploadfile/{hostname}")
async def create_upload_file(hostname: str, file: UploadFile = File(...)):
    filedata = await file.read()
    return await items.send_file_to_machine(hostname, file.filename, filedata)
