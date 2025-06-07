import asyncio
from typing import Union, List, Dict, Any
from astarmiko.base import Activka, setup_config, send_commands, ping_one_ip
import logging
import json
from tqdm.asyncio import tqdm_asyncio
from astarmiko.optional_loggers import forward_log_entry

def is_reachable(ip: str) -> bool:
    return ping_one_ip(ip) == 0

class DeviceLogCapture:
    def __init__(self, device, use_rsyslog=False, use_loki=False,
                 use_elastic=False):
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
            forward_log_entry(entry, rsyslog=self.use_rsyslog,
                              loki=self.use_loki,
                              elastic=self.use_elastic)

class ActivkaAsync(Activka):
    async def execute_on_devices(self, devices: Union[str, List[str]],
                                 commands: Union[str, List[str],
                                                 Dict[str, List[str]]],
                                 rsyslog=False, loki=False,
                                 elastic=False, use_template=False) -> Dict[str, Any]:

        from astarmiko.base import ac
        if isinstance(devices, str):
            devices = [devices]

        results = {'success': {}, 'failed': {}, 'unreachable': []}

        async def worker(device_name):
            log = DeviceLogCapture(device_name, rsyslog, loki, elastic)
            try:
                device = self.choose(device_name, withoutname=True)
                if not is_reachable(device['ip']):
                    log.log("Unreachable (ICMP fail)")
                    results['unreachable'].append(device_name)
                    return

                device_type = device.get("device_type")
                if commands[0] in ac.commands:
                    cmd_list = ac.commands[commands[0]][device_type]
                else:
                    cmd_list = commands.get(device_type, []) if isinstance(commands, dict) else commands
                log.log(f"Connecting to {device['ip']}")
                output = []
                for cmd in cmd_list:
                    res = send_commands(device, cmd, mode='exec')
                    if use_template:
                        tmpl = ac.commands.get(cmd, {}).get(device_type)
                        if tmpl:
                            parsed = templatizator(res, cmd, device_type)
                            output.append(parsed)
                        else:
                            output.append(res)
                    else:
                        output.append(res)

                results['success'][device_name] = '\n'.join(output)
                log.log("Commands are successfully executed")
            except Exception as e:
                results['failed'][device_name] = str(e)
                log.log(f"Error: {e}", level=logging.ERROR)
            finally:
                log.flush()

        await tqdm_asyncio.gather(*(worker(dev) for dev in devices),
                                  desc="Executing show commands")
        return results

    async def setconfig_on_devices(self, devices: Union[str, List[str]],
                                   commands: Union[str, List[str],
                                                   Dict[str, List[str]]],
                                   rsyslog=False, loki=False,
                                   elastic=False) -> Dict[str, Any]:
        if isinstance(devices, str):
            devices = [devices]

        results = {'success': {}, 'failed': {}, 'unreachable': []}

        async def worker(device_name):
            log = DeviceLogCapture(device_name, rsyslog, loki, elastic)
            try:
                device = self.choose(device_name, withoutname=True)
                if not is_reachable(device['ip']):
                    log.log("Unreachable (ICMP fail)")
                    results['unreachable'].append(device_name)
                    return

                device_type = device.get("device_type")
                cmd_list = commands.get(device_type, []) if isinstance(commands, dict) else commands
                log.log(f"Connecting to {device['ip']}")
                result = send_commands(device, cmd_list, mode='config')
                results['success'][device_name] = result
                log.log("The configuration has been successfully applied")
            except Exception as e:
                results['failed'][device_name] = str(e)
                log.log(f"Error: {e}", level=logging.ERROR)
            finally:
                log.flush()

        await tqdm_asyncio.gather(*(worker(dev) for dev in devices), desc="Executing config commands")
        return results

