#!/usr/bin/python3

import psutil
import pylxd
client = pylxd.Client()


def get_all_container_name():
    return [container.name for container in client.containers.all()]


def launch_container_machine(name, port):
    config = {
        "name": name,
        "source": {"type": "image", "fingerprint": "9ea515314bcd2f23c1d7"},
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


def check_port_available(port):
    # "LISTEN" 状態のポート番号をリスト化
    used_ports = [conn.laddr.port for conn in psutil.net_connections()
                  if conn.status == 'LISTEN']
    if (port in used_ports):
        return False
    else:
        return True


def read_file(file_path):
    with open(file_path) as f:
        l_strip = [s.strip() for s in f.readlines()]
        return l_strip


def make_csv(
        in_file_path,
        out_file_path,
        start_port,
        prefix="",
        suffix="",
        image_aliases="",
        image_fingerprint=""):
    members = read_file(in_file_path)
    port_offset = 0
    file_meta = ["hostname,port,image_aliases,image_fingerprint"]
    for i in range(len(members)):
        while True:
            port_candidate = start_port + i + port_offset
            if check_port_available(port_candidate):
                file_meta.append(
                    prefix +
                    members[i] +
                    suffix +
                    "," +
                    str(port_candidate) +
                    "," +
                    image_aliases +
                    "," +
                    image_fingerprint

                )
                break
            else:
                port_offset += 1
    with open(out_file_path, mode='w') as f:
        f.write('\n'.join(file_meta))


if __name__ == "__main__":
    make_csv(
        'member.txt',
        'member.csv',
        10000,
        prefix="PIT0014-",
        image_aliases="PIT0014-v1")
    for line in read_file('member.csv')[1:]:
        hostname, port, aliases, fingerprint = line.split(",")
        print(hostname, port, aliases, fingerprint)
    launch_container_machine(hostname, port)
    # launch_container_machine("my-test2","5659")
    # delete_machine("my-vmapitest")
