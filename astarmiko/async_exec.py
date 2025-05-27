# async_exec.py
import asyncio
from typing import Union, List, Dict, Any
from astarmiko.base import Activka, setup_config, send_show_command, send_config_commands
from astarmiko.base import ping_one_ip

def is_reachable(ip: str) -> bool:
    return ping_one_ip(ip) == 0

class ActivkaAsync(Activka):
    async def execute_on_devices(self, devices: Union[str, List[str]], commands: Union[str, List[str]]) -> Dict[str, Any]:
        if isinstance(devices, str):
            devices = [devices]
        if isinstance(commands, str):
            commands = [commands]

        results = {
            'success': {},
            'failed': {},
            'unreachable': []
        }

        async def worker(device_name):
            device = self.choose(device_name, withoutname=True)
            if not is_reachable(device['ip']):
                results['unreachable'].append(device_name)
                return
            try:
                output = []
                for cmd in commands:
                    res = send_show_command(device, cmd)
                    output.append(res)
                results['success'][device_name] = '\n'.join(output)
            except Exception as e:
                results['failed'][device_name] = str(e)

        await asyncio.gather(*(worker(dev) for dev in devices))
        return results

    async def setconfig_on_devices(self, devices: Union[str, List[str]], commands: Union[str, List[str]]) -> Dict[str, Any]:
        if isinstance(devices, str):
            devices = [devices]
        if isinstance(commands, str):
            commands = [commands]

        results = {
            'success': {},
            'failed': {},
            'unreachable': []
        }

        async def worker(device_name):
            device = self.choose(device_name, withoutname=True)
            if not is_reachable(device['ip']):
                results['unreachable'].append(device_name)
                return
            try:
                result = send_config_commands(device, commands)
                results['success'][device_name] = result
            except Exception as e:
                results['failed'][device_name] = str(e)

        await asyncio.gather(*(worker(dev) for dev in devices))
        return results

# === Example of using ===
if __name__ == "__main__":
    import sys

    async def main():
        setup_config("astarmiko.yml")
        a = ActivkaAsync("activka_byname.yaml")

        devices = ["C2911KIRPICH", "C2911MRES"]
        show_cmds = ["show version"]
        config_cmds = ["interface lo1", "description Test"]

        print("--- EXECUTING SHOW ---")
        result = await a.execute_on_devices(devices, show_cmds)
        print(result)

        print("--- EXECUTING CONFIG ---")
        result = await a.setconfig_on_devices(devices, config_cmds)
        print(result)

    asyncio.run(main())

