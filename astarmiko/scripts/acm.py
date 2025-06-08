#!/usr/bin/env python3
# acm.py - Async CLI для astarmiko
import argparse
import asyncio
import json
from astarmiko.async_exec import ActivkaAsync
from astarmiko.base import setup_config
from astarmiko.log_config import get_log_config, setup_logging

async def async_main():
    parser = argparse.ArgumentParser(description="AstarMiko Async CLI")
    parser.add_argument("command", choices=["show", "set"], help="Operation to perform")
    parser.add_argument("--device", nargs="+", required=True, help="Device name(s)")
    parser.add_argument("--cmd", help="Command as string or JSON")
    parser.add_argument("--cmd-file", help="Path to file with commands in JSON format")
    parser.add_argument("--conf", default="astarmiko.yml", help="Config file path")
    parser.add_argument("--rsyslog", action="store_true")
    parser.add_argument("--loki", action="store_true")
    parser.add_argument("--elastic", action="store_true")

    args = parser.parse_args()
    setup_config(args.conf)
    
    from astarmiko.base import ac
    
    logcfg = get_log_config(args.conf)
    setup_logging(logcfg)

    a = ActivkaAsync("activka_byname.yaml", ac)
    
    # Определяем команды
    commands = None
    use_template = False
    if args.cmd_file:
        try:
            with open(args.cmd_file, "r", encoding="utf-8") as f:
                commands = json.load(f)
        except Exception as e:
            print(f"Failed to load --cmd-file: {e}")
            return
    elif args.cmd:
        # Если команда есть в справочнике ac.commands - используем шаблон
        if args.cmd in ac.commands:
            use_template = True
            commands = [args.cmd]
        else:
            commands = [args.cmd]
    else:
        print("Either --cmd or --cmd-file must be provided")
        return

    # Преобразуем имена устройств к правильному написанию (если есть в inventory)
    real_devices = []
    for dev in args.device:
        real_name = a.find_real_device_name(dev)
        if real_name:
            real_devices.append(real_name)
        else:
            print(f"Device '{dev}' not found in inventory. Skipping.")

    if not real_devices:
        print("No valid devices to process. Exiting.")
        return

    # Выполняем команду
    if args.command == "show":
        result = await a.execute_on_devices(
            real_devices, commands,
            rsyslog=args.rsyslog,
            loki=args.loki,
            elastic=args.elastic,
            use_template=use_template
        )
    elif args.command == "set":
        result = await a.setconfig_on_devices(
            real_devices, commands,
            rsyslog=args.rsyslog,
            loki=args.loki,
            elastic=args.elastic
        )

    print(json.dumps(result, indent=2, ensure_ascii=False))

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()

