import paramiko
import os 
import asyncio
from sshtunnel import SSHTunnelForwarder

def _ssh_connect():
    if not hasattr(paramiko, "DSSKey"):
        paramiko.DSSKey = paramiko.PKey
    ssh_config = paramiko.SSHConfig()
    with open(os.path.expanduser("~/.ssh/config")) as f:
        ssh_config.parse(f)
    
    host_config = ssh_config.lookup("ollama-tunnel")

    forward_info = host_config.get("localforward", ["11434 127.0.0.1:11434"])[0].split()
    local_port = int(forward_info[0])
    remote_host, remote_port = forward_info[1].split(":")

    tunnel = None
    try:
        tunnel = SSHTunnelForwarder(
            (host_config["hostname"], int(host_config.get("port", 22))),
            ssh_username=host_config.get("user"),
            ssh_password=os.getenv("SSH_PASSWORD"),
            ssh_pkey=None,
            remote_bind_address=(remote_host, int(remote_port)),
            local_bind_address=("127.0.0.1", local_port)
        )
        tunnel.start()
    except Exception as e:
        print(e)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host_config["hostname"],
        username=host_config.get("user"),
        port=int(host_config.get("port", 22)),
        key_filename=host_config.get("identityfile", None),
        password=os.getenv("SSH_PASSWORD"),
    ) 
    
    return client, tunnel

async def run_remote():
    # paramiko è sincrono, lo eseguiamo in un thread separato
    loop = asyncio.get_event_loop()
    client, tunnel = await loop.run_in_executor(None, _ssh_connect)
    return client, tunnel

async def close_remote(client, tunnel):
    if tunnel is not None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, tunnel.stop)
        print("Tunnel SSH fermato con successo.")
    if client is not None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, client.close)
        print("Client SSH chiuso con successo.")

    