#!/usr/bin/python3

import inspect
import asyncio
import os
import socket
import time

import aiohttp
import netifaces as ni
import psutil
import pylxd
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import asyncio
from functools import wraps, partial
import shlex

# 同期関数を非同期関数にする


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


# スケジューラー
Schedule = AsyncIOScheduler()
Schedule.start()


# lxdクライアント
client = pylxd.Client()


def make_response_dict(
    status=True,
    details="success",
    assign_port="",
    option=""
):
    return {
        "status": status,
        "details": details,
        "assign_port": assign_port,
        "option": option
    }


# マシンコマンド実行
async def exec_command_to_machine(hostname, cmd):
    machine = get_machine(hostname)
    if machine is None:
        raise Exception("マシンが見つかりません")
    async_machine_execute = async_wrap(machine.execute)
    result = await async_machine_execute(shlex.split(cmd))
    return result


async def launch_machine(
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
):
    # ローカルイメージ検索
    aliases, fingerprint = get_all_image()
    if (imagealias == "") and (imagefinger == ""):
        # raise Exception("イメージが指定されていません")
        return make_response_dict(False, "image_error", "イメージが指定されていません")

    elif imagealias != "" and len([s for s in aliases if imagealias == s]) == 0:
        # raise Exception("イメージ名が異なっています")
        return make_response_dict(False, "image_error", "イメージエイリアスが異なっています")
    elif imagefinger != "" and len([s for s in fingerprint if s.startswith(imagefinger)]) == 0:
        # raise Exception("イメージ名が異なっています")
        return make_response_dict(
            False, "image_error", "イメージフィンガープリントが異なっています")

    # マシンが無ければ新規作成
    machine = get_machine(hostname)
    assign_port = None
    if None is machine:
        # コンテナであれば
        if machinetype == "container":
            assign_port = scan_available_port(int(startportassign))
            print("なし")
            launch_container_machine(
                hostname=hostname,
                srcport=srcport,
                dstport=assign_port,
                cpu=cpu,
                memory=memory,
                fingerprint=imagefinger,
                aliases=imagealias
            )

            print(get_ip())
            pass
        # それ以外は仮想マシン
        else:
            pass
    # マシンが存在場合
    else:
        remove_stop_machine_schedule(hostname)
        if len(get_machine_used_port(hostname)) != 0:
            assign_port = get_machine_used_port(hostname)[0]

        if machine.status == "Running":

            if await wait_get_html(make_url(assign_port), httpstatus, 5):
                pass
            else:
                machine.restart()
        else:
            machine.start()

    # 起動確認
    if "1" == startcheck:
        result = await wait_get_html(
            make_url(assign_port),
            httpstatus,
            starttimeout
        )
        if result:
            return make_response_dict(assign_port=assign_port)
        else:
            return make_response_dict(False, "timeout_error")
    else:
        return make_response_dict(assign_port=assign_port)


def make_url(assign_port):
    # URL生成
    try_url = ""
    if https == "0":
        try_url += "http://"
    else:
        try_url += "https://"
    try_url += "127.0.0.1"
    try_url += ":" + str(assign_port)
    return try_url


async def wait_get_html(url, status, time_out):
    start_time = time.time()
    while time.time() - start_time < time_out:
        result = await get_html(url)
        if str(result) == str(status):
            return True
        await asyncio.sleep(1)
    return False


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, verify_ssl=False) as resp:
                return int(resp.status)
        except aiohttp.client_exceptions.ClientConnectorError:
            return 0


def get_all_image():
    aliases = []
    fingerprint = []
    for image in client.images.all():
        if len(image.aliases) != 0:
            for i in image.aliases:
                if "name" in i:
                    aliases.append(i["name"])
        fingerprint.append(image.fingerprint)
    return aliases, fingerprint


def get_all_machine_name():
    A = []
    B = [container.name for container in client.containers.all()]
    C = [virtual_machine.name for virtual_machine in client.virtual_machines.all()]
    A.extend(B)
    A.extend(C)
    return A


def launch_container_machine(
        hostname="",
        srcport="",
        dstport="",
        cpu="2",
        memory="4GB",
        fingerprint="",
        aliases=""):
    image = {}
    if fingerprint != "":
        image = {"type": "image", "fingerprint": str(fingerprint)}
    elif aliases != "":
        image = {"type": "image", "aliases": str(aliases)}
    config = {
        "name": str(hostname),
        "source": image,
        "config": {"limits.cpu": str(cpu), "limits.memory": str(memory)},
        "devices": {
            "vscode-port": {
                "bind": "host",
                "connect": "tcp:127.0.0.1:" + str(srcport),
                "listen": "tcp:0.0.0.0:" + str(dstport),
                "type": "proxy"}
        }
    }
    container = client.containers.create(config, wait=True)
    container.start()


def launch_virtual_machine():
    config = {
        "name": "my-vmapitest",
        "source": {
            "type": "image",
            "fingerprint": "fbca989572df"},
        "config": {
            "limits.cpu": "2",
            "limits.memory": "3GB"},
        "devices": {
            "root": {
                "path": "/",
                "pool": "default",
                "type": "disk",
                "size": "20GB"}}}
    virtual_machines = client.virtual_machines.create(config, wait=True)
    virtual_machines.start(wait=True)


def get_machine(name):
    machine = None
    try:
        machine = client.containers.get(name)
    except pylxd.exceptions.NotFound:
        pass
    try:
        machine = client.virtual_machines.get(name)
    except pylxd.exceptions.NotFound:
        pass
    return machine


# マシンストップスケジューラー
def add_stop_machine_schedule(machine_name, delay):
    if delay < 5:
        delay = 5
    try:
        schedule_job = Schedule.add_job(
            lambda: stop_machine(machine_name, call_from_scheduler=True),
            trigger='interval',
            seconds=delay,
            id=machine_name + "-stop-scheduled"
        )
    except BaseException:
        return make_response_dict(False, "existing_job")
    return make_response_dict()


def remove_stop_machine_schedule(machine_name):
    try:
        Schedule.remove_job(machine_name + "-stop-scheduled")
    except BaseException:
        return make_response_dict(False, "job_not_found")
    return make_response_dict()


def get_stop_machine_schedule():
    schedules = []
    for job in Schedule.get_jobs():
        schedules.append(
            {
                "Name": str(job.id),
                "Run Frequency": str(job.trigger),
                "Next Run": str(job.next_run_time)
            }
        )
    return make_response_dict(details=schedules)


def stop_machine(machine_name, call_from_scheduler=False):
    if call_from_scheduler:
        remove_stop_machine_schedule(machine_name)
    machine = get_machine(machine_name)
    if machine is None:
        return False
    try:
        machine.stop()
    except BaseException:
        return False
    return True


def start_machine(name):
    machine = get_machine(name)
    if machine is None:
        return False
    machine.start()


def delete_machine(name):
    print(get_machine(name))


def get_machine_used_port(machine_name):
    machine = get_machine(machine_name)
    if machine is None:
        return []
    used_ports = []
    for key in machine.devices:
        if "type" in machine.devices[key]:
            if machine.devices[key]["type"] == "proxy":
                used_ports.append(
                    int(machine.devices[key]["connect"].split(":")[-1]))
    return used_ports


def get_used_port():
    """
    現在利用中のportと割り当て済みのport一覧作成
    """
    used_ports = [int(conn.laddr.port) for conn in psutil.net_connections()
                  if conn.status == 'LISTEN']
    for machine in client.containers.all():
        for key in machine.devices:
            if "type" in machine.devices[key]:
                if machine.devices[key]["type"] == "proxy":
                    used_ports.append(
                        int(machine.devices[key]["connect"].split(":")[-1]))

    for machine in client.virtual_machines.all():
        for key in machine.devices:
            if "type" in machine.devices[key]:
                if machine.devices[key]["type"] == "proxy":
                    used_ports.append(
                        int(machine.devices[key]["connect"].split(":")[-1]))
    used_ports = sorted(set(used_ports))
    return used_ports


def check_port_available(port):
    used_ports = get_used_port()
    if (port in used_ports):
        return False
    else:
        return True


def scan_available_port(start_port):
    port_offset = 0
    used_ports = get_used_port()
    while True:
        port_candidate = start_port + port_offset
        if port_candidate in used_ports:
            port_offset += 1
        else:
            return port_candidate
        if port_candidate > 65535:
            raise Exception("利用可能なport上限を超えました")


def get_ip() -> list:
    if os.name == "nt":
        # Windows
        return socket.gethostbyname_ex(socket.gethostname())[2]
        pass
    else:
        # それ以外
        result = []
        address_list = psutil.net_if_addrs()
        for nic in address_list.keys():
            ni.ifaddresses(nic)
            try:
                ip = ni.ifaddresses(nic)[ni.AF_INET][0]['addr']
                if ip not in ["127.0.0.1"]:
                    result.append(ip)
            except KeyError as err:
                pass
        return result


def read_file(file_path):
    with open(file_path) as f:
        l_strip = [s.strip() for s in f.readlines()]
        return l_strip


def make_csv(
        in_file_path,
        out_file_path,
        start_port=0,
        prefix="",
        suffix="",
        image_aliases="",
        image_fingerprint="",
        class_code="",
        ip_address=""):
    members = read_file(in_file_path)
    port_offset = 0
    file_meta = ["class_code,name,ip,port,image_aliases,image_fingerprint"]
    for i in range(len(members)):
        while True:
            port_candidate = start_port + i + port_offset
            if check_port_available(port_candidate):
                file_meta.append(
                    class_code + "," +
                    members[i] + "," +
                    ip_address + "," +
                    str(port_candidate) + "," +
                    image_aliases + "," +
                    image_fingerprint
                )
                break
            else:
                port_offset += 1
    with open(out_file_path, mode='w') as f:
        f.write('\n'.join(file_meta))


def make_csv_from_str(
        in_file_str="",
        start_port=0,
        prefix="",
        suffix="",
        image_aliases="",
        image_fingerprint="",
        class_code="",
        ip_address=""):
    members = in_file_str.splitlines()
    port_offset = 0
    file_meta = ["class_code,name,ip,port,image_aliases,image_fingerprint"]
    for i in range(len(members)):
        while True:
            port_candidate = start_port + i + port_offset
            if check_port_available(port_candidate):
                file_meta.append(
                    class_code + "," +
                    members[i] + "," +
                    ip_address + "," +
                    str(port_candidate) + "," +
                    image_aliases + "," +
                    image_fingerprint
                )
                break
            else:
                port_offset += 1
    return '\n'.join(file_meta)


def get_machine_file(machine_name, file_path, local_path):
    machine = get_machine(machine_name)
    file_meta = machine.files.recursive_get(file_path, local_path)

    return file_meta


async def test():
    hoge = await wait_get_html("https://yukkuriikouze.com", 200, 5)
    print(hoge)


async def test():
    await asyncio.gather(exec_command_to_machine("funo", "sleep 10"),exec_command_to_machine("funo", "sleep 10"),exec_command_to_machine("funo", "sleep 10"))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())


"""
make_csv(
        'member.txt',
        'member.csv',
        start_port=10000,
        ip_address="160.252.131.148",
        class_code="PIT0014",
        image_aliases="PIT0014-v1")
    for line in read_file('member.csv')[1:]:
        class_code, name, ip, port, aliases, fingerprint = line.split(",")
        #print(class_code+"-"+name, port, aliases, fingerprint)
        print("launch"+class_code+"-"+name)
        #launch_container_machine(class_code+"-"+name, port)
    # launch_container_machine("my-test2","5659")
    # delete_machine("my-vmapitest")
"""
