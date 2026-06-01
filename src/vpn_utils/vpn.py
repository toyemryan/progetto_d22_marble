import asyncio
import subprocess
from contextlib import asynccontextmanager

async def vpn_connect():
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-Command",
        "Start-Process wireguard -ArgumentList '/installtunnelservice C:/Users/simon/.ssh/wg_Progetto_CV.conf' -Verb RunAs -Wait"
    )
    await proc.wait()
    
    # Aspetta finché la VPN è davvero su
    for _ in range(10):
        result = subprocess.run(
            ["ping", "-n", "1", "192.168.80.138"],
            capture_output=True
        )
        if result.returncode == 0:
            return
        await asyncio.sleep(1)
    
    raise RuntimeError("VPN non raggiungibile dopo 10 secondi")

async def vpn_disconnect():
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-Command",
        "Start-Process wireguard -ArgumentList '/uninstalltunnelservice wg_Progetto_CV' -Verb RunAs -Wait"
    )
    await proc.wait()

@asynccontextmanager
async def vpn_tunnel():
    await vpn_connect()
    try:
        yield
    finally:
        await vpn_disconnect()