import yaml
import asyncio
from astarmiko.base import (
    setup_config,
    setup_logging,
    )

async def main():
    setup_config('/home/mypython/astarmiko.yml')
    from astarmiko.async_exec_2 import ActivkaAsync
    from astarmiko.base import ac
    
    acl_commands = '/home/mypython/setACL.yml'
    devices = ['c2911Letnyaya','rpb-s5731']
    with open(acl_commands) as f:
        acl_cmd = yaml.safe_load(f)
    
    a = ActivkaAsync("activka_byname.yaml")
    result = await a.setconfig_on_devices(devices, acl_cmd)
    print(result)

asyncio.run(main())
