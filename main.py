import asyncio
import datetime
import json
import random
import string
#import aiofiles

from fastapi import FastAPI
import items


app = FastAPI()


@app.get("/")
async def request_all_container_name():
    return items.get_all_container_name()


@app.post("/launch_container")
async def request_launch_container(config: dict):
    return items.get_all_container_name()


@app.get("/launch_test")
async def request_launch_container_machine():
    return items.launch_container()


@app.get("/start")
async def request_launch_container_machine(name: str):
    return items.start_machine(name)


@app.get("/stop")
async def request_launch_container_machine(name: str):
    return items.stop_machine(name)
