#!/usr/bin/env python3
# async_exec.py
import asyncio
from typing import Union, List, Dict, Any
from astarmiko.base import Activka, setup_config, send_commands, templatizator, ac
import logging
import json
import os
from tqdm.asyncio import tqdm_asyncio
from astarmiko.optional_loggers import forward_log_entry

async def is_device_available(ip: str) -> bool:
    """
    Asynchronous ICMP ping to check if device is reachable.
    """
    if os.name == "nt":
        args = ["ping", "-n", "3", ip]
    else:
        args = ["ping", "-c", "3", ip]
    proc = await asyncio.create_subprocess_exec(*args,
                                                stdout=asyncio.subprocess.DEVNULL,
                                                stderr=asyncio.subprocess.DEVNULL)
    await proc.communicate()
    return proc.returncode == 0

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
    """
    Activka based class with asynchronous wrapper
    """

    def __init__(self, byname, ac_config, *args):
        super().__init__(byname, *args)
        self.ac = ac_config  # сохраним объект Astarconf в атрибуте


    async def execute_on_devices(self, devices: Union[str, List[str]], commands: Union[str, List[str], Dict[str, List[str]]],
                                 rsyslog=False, loki=False, elastic=False, use_template=False) -> Dict[str, Any]:
        if isinstance(devices, str):
            devices = [devices]

        results = {'success': {}, 'failed': {}, 'unreachable': []}

        async def worker(device_name):
            log = DeviceLogCapture(device_name, rsyslog, loki, elastic)
            try:
                device = self.choose(device_name, withoutname=True)
                if not await is_device_available(device['ip']):
                    log.log("Unreachable (ICMP fail)")
                    results['unreachable'].append(device_name)
                    return

                device_type = device.get("device_type")
                cmd_list = commands.get(device_type, []) if isinstance(commands, dict) else commands

                log.log(f"Connecting to {device['ip']}")
                output = []
                if use_template:
                    cmd_list = self.ac.commands.get(cmd, {}).get(device_type)
                if cmd_list:
                    for cmd in cmd_list:
                        res = send_commands(device, cmd, mode='exec')
                        if use_template:
                            parsed = templatizator(res, commands, device_type)
                            output.append(parsed)
                        else:
                            output.append(res)

                results['success'][device_name] = output if len(output) > 1 else output[0]
                log.log("Commands are successfully executed")
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

        results = {'success': {}, 'failed': {}, 'unreachable': []}

        async def worker(device_name):
            log = DeviceLogCapture(device_name, rsyslog, loki, elastic)
            try:
                device = self.choose(device_name, withoutname=True)
                if not await is_device_available(device['ip']):
                    log.log("Unreachable (ICMP fail)")
                    results['unreachable'].append(device_name)
                    return

                device_type = device.get("device_type")
                cmd_list = commands.get(device_type, []) if isinstance(commands, dict) else commands

                log.log(f"Connecting to {device['ip']}")
                result = send_commands(device, cmd_list, mode='config')
                results['success'][device_name] = result
                log.log("Commands are successfully executed")
            except Exception as e:
                results['failed'][device_name] = str(e)
                log.log(f"Ошибка: {e}", level=logging.ERROR)
            finally:
                log.flush()

        await tqdm_asyncio.gather(*(worker(dev) for dev in devices), desc="Executing config commands")
        return results

