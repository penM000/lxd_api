#!/usr/bin/python3

import pylxd
client = pylxd.Client()


def get_all_container_name():
    return [container.name for container in client.containers.all()]


def launch_container_machine(name, port):
    config = {
        "name": name,
        "source": {"type": "image", "fingerprint": "36018660665e"},
        "config": {"limits.cpu": "2", "limits.memory": "3GB"},
        "devices": {
            "vscode-port": {
                "bind": "host",
                "connect": "tcp:127.0.0.1:8080",
                "listen": "tcp:0.0.0.0:" + str(port),
                "type": "proxy"}
        }
    }
    container = client.containers.create(config, wait=True)
    container.start(wait=True)


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
    virtual_machines.start()


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


def stop_machine(name):
    machine = get_machine(name)
    if machine is None:
        return False
    machine.stop()


def start_machine(name):
    machine = get_machine(name)
    if machine is None:
        return False
    machine.start()


def delete_machine(name):
    print(get_machine(name))


if __name__ == "__main__":
    launch_container_machine("my-test2","5659")
    #delete_machine("my-vmapitest")
