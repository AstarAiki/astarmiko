# async_exec.py
import asyncio
from typing import Union, List, Dict, Any
from astarmiko.base import Activka, setup_config, send_show_command, send_config_commands
from astarmiko.base import ping_one_ip
import logging
from io import StringIO
import json
from tqdm.asyncio import tqdm_asyncio
from optional_loggers import forward_log_entry

def is_reachable(ip: str) -> bool:
    return ping_one_ip(ip) == 0

class DeviceLogCapture:
    def __init__(self, device, use_rsyslog=False, use_loki=False, use_elastic=False):
        self.device = device
        self.buffer = []
        self.logger = logging.getLogger()
        self.use_rsyslog = use_rsyslog
        self.use_loki = use_loki
        self.use_elastic = use_elastic

    def log(self, msg, level=logging.INFO):
        entry = {
            "device": self.device,
            "level": logging.getLevelName(level),
            "message": msg
        }
        self.buffer.append(entry)

    def flush(self):
        for entry in self.buffer:
            self.logger.info(json.dumps(entry, ensure_ascii=False))
            forward_log_entry(entry, rsyslog=self.use_rsyslog, loki=self.use_loki, elastic=self.use_elastic)

class ActivkaAsync(Activka):
    async def execute_on_devices(self, devices: Union[str, List[str]], commands: Union[str, List[str], Dict[str, List[str]]],
                                 rsyslog=False, loki=False, elastic=False) -> Dict[str, Any]:
        if isinstance(devices, str):
            devices = [devices]

        results = {
            'success': {},
            'failed': {},
            'unreachable': []
        }

        async def worker(device_name):
            log = DeviceLogCapture(device_name, rsyslog, loki, elastic)
            try:
                device = self.choose(device_name, withoutname=True)
                if not is_reachable(device['ip']):
                    log.log("Недоступен (ICMP fail)")
                    results['unreachable'].append(device_name)
                    return

                device_type = device.get("device_type")
                cmd_list = commands.get(device_type, []) if isinstance(commands, dict) else commands

                log.log(f"Подключаюсь к {device['ip']}")
                output = []
                for cmd in cmd_list:
                    res = send_show_command(device, cmd)
                    output.append(res)
                results['success'][device_name] = '\n'.join(output)
                log.log("Команды успешно выполнены")
            except Exception as e:
                results['failed'][device_name] = str(e)
                log.log(f"Ошибка: {e}", level=logging.ERROR)
            finally:
                log.flush()

        await tqdm_asyncio.gather(*(worker(dev) for dev in devices), desc="Executing show commands")
        return results

    async def setconfig_on_devices(self, devices: Union[str, List[str]], commands: Union[str, List[str], Dict[str, List[str]]],
                                   rsyslog=False, loki=False, elastic=False) -> Dict[str, Any]:
        if isinstance(devices, str):
            devices = [devices]

        results = {
            'success': {},
            'failed': {},
            'unreachable': []
        }

        async def worker(device_name):
            log = DeviceLogCapture(device_name, rsyslog, loki, elastic)
            try:
                device = self.choose(device_name, withoutname=True)
                if not is_reachable(device['ip']):
                    log.log("Недоступен (ICMP fail)")
                    results['unreachable'].append(device_name)
                    return

                device_type = device.get("device_type")
                cmd_list = commands.get(device_type, []) if isinstance(commands, dict) else commands

                log.log(f"Подключаюсь к {device['ip']}")
                result = send_config_commands(device, cmd_list)
                results['success'][device_name] = result
                log.log("Конфигурация успешно применена")
            except Exception as e:
                results['failed'][device_name] = str(e)
                log.log(f"Ошибка: {e}", level=logging.ERROR)
            finally:
                log.flush()

        await tqdm_asyncio.gather(*(worker(dev) for dev in devices), desc="Executing config commands")
        return results

# === Example of using ===
if __name__ == "__main__":
    import sys

    async def main():
        setup_config("astarmiko.yml")
        a = ActivkaAsync("activka_byname.yaml")

        devices = ["C2911KIRPICH", "C2911MRES"]
        show_cmds = {"cisco_ios": ["show version"], "huawei": ["display version"]}
        config_cmds = {
            "cisco_ios": ["line vty 0 15", "no access-class MGMT_ACCESS in", "exit"],
            "huawei": ["user-interface vty 0 4", "undo acl name MGMT_ACCESS", "q"]
        }

        print("--- EXECUTING SHOW ---")
        result = await a.execute_on_devices(devices, show_cmds, rsyslog=True)
        print(result)

        print("--- EXECUTING CONFIG ---")
        result = await a.setconfig_on_devices(devices, config_cmds, loki=True)
        print(result)

    asyncio.run(main())

