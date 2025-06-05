# cli.py
import argparse
import asyncio
import json
from astarmiko.async_exec import ActivkaAsync
from astarmiko.base import setup_config
from astarmiko.log_config import get_log_config, setup_logging


async def main():
    parser = argparse.ArgumentParser(description="AstarMiko Async CLI")
    parser.add_argument("command", choices=["show", "set"],
                        help="Operation to perform")
    parser.add_argument("--device", nargs="+", required=True,
                        help="Device name(s)")
    parser.add_argument("--cmd", help="Command as string or JSON")
    parser.add_argument("--cmd-file",
                        help="Path to file with commands in JSON format")
    parser.add_argument("--conf", default="astarmiko.yml",
                        help="Config file path")
    parser.add_argument("--rsyslog", action="store_true")
    parser.add_argument("--loki", action="store_true")
    parser.add_argument("--elastic", action="store_true")

    args = parser.parse_args()
    setup_config(args.conf)
    logcfg = get_log_config()
    setup_logging(logcfg)

    a = ActivkaAsync("activka_byname.yaml")

    commands = None
    if args.cmd_file:
        try:
            with open(args.cmd_file, "r", encoding="utf-8") as f:
                commands = json.load(f)
        except Exception as e:
            print(f"Failed to load --cmd-file: {e}")
            return
    elif args.cmd:
        try:
            commands = (
                json.loads(args.cmd) if args.cmd.strip().startswith("{")
                else [args.cmd]
            )
        except Exception as e:
            print(f"Failed to parse --cmd: {e}")
            return
    else:
        print("Either --cmd or --cmd-file must be provided")
        return

    if args.command == "show":
        result = await a.execute_on_devices(
            args.device,
            commands,
            rsyslog=args.rsyslog,
            loki=args.loki,
            elastic=args.elastic,
        )
    elif args.command == "set":
        result = await a.setconfig_on_devices(
            args.device,
            commands,
            rsyslog=args.rsyslog,
            loki=args.loki,
            elastic=args.elastic,
        )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
