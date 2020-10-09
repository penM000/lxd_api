from pylxd import Client
client = Client()
#config = {'name': 'my-containerapitest', 'source':  {'type': 'image', 'fingerprint': '4746a4889a31'},'config': {'limits.cpu': '2'}}
#config = {'name': 'my-container', 'source': {'type': 'none'}}
#container = client.containers.create(config, wait=True)
#container.start()
#container = client.virtual_machines.get('ubuntu')
#container.ephemeral = False
#container.devices = { 'root': { 'path': '/', 'type': 'disk', 'size': '7GB'} }
#container.save()

config = {'name': 'my-vmapitest', 'source':  {'type': 'image', 'fingerprint': 'fbca989572df'},'config': {'limits.cpu': '2','limits.memory': '3GB'},'devices':{ 'root': { 'path': '/', 'pool':'default','type': 'disk', 'size': '20GB'} }}
virtual_machines = client.virtual_machines.create(config, wait=True)
virtual_machines.start()