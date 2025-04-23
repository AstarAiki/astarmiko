# manage.py
import argparse
from astarmiko import base
from astarmiko.base import Activka, setup_config

def main():
    parser = argparse.ArgumentParser(description="AstarMiko CLI Utility")
    subparsers = parser.add_subparsers(dest="command")

    # Подкоманда: backup
    backup_parser = subparsers.add_parser("backup", help="Получить текущий конфиг устройства")
    backup_parser.add_argument("--device", required=True)
    backup_parser.add_argument("--conf", default="astarmiko.yml")

    # Подкоманда: show
    show_parser = subparsers.add_parser("show", help="Выполнить show-команду")
    show_parser.add_argument("--device", required=True)
    show_parser.add_argument("--cmd", required=True)
    show_parser.add_argument("--conf", default="astarmiko.yml")

    # Подкоманда: set
    set_parser = subparsers.add_parser("set", help="Выполнить конфигурационную команду")
    set_parser.add_argument("--device", required=True)
    set_parser.add_argument("--cmd", required=True)
    set_parser.add_argument("--log", action="store_true")
    set_parser.add_argument("--conf", default="astarmiko.yml")

    # Подкоманда: filter
    filter_parser = subparsers.add_parser("filter", help="Фильтрация устройств по параметрам")
    filter_parser.add_argument("--segment", nargs='*')
    filter_parser.add_argument("--level", nargs='*')
    filter_parser.add_argument("--type", nargs='*')
    filter_parser.add_argument("--conf", default="astarmiko.yml")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    setup_config(args.conf)
    a = Activka("activka_byname.yaml")

    if args.command == "backup":
        config = a.get_curr_config(args.device)
        print('\n'.join(config))

    elif args.command == "show":
        result = a.getinfo(args.device, args.cmd, othercmd=True)
        if isinstance(result, list):
            for line in result:
                print(line)
        else:
            print(result)

    elif args.command == "set":
        result = a.setconfig(args.device, args.cmd.split(';'), log=args.log)
        print(result)

    elif args.command == "filter":
        result = a.filter(
            segment=args.segment,
            levels=args.level,
            device_type=args.type
        )
        print("Найдено устройств:", len(result))
        for name, data in result.items():
            print(f"{name} ({data['ip']}) - {data['device_type']}")

if __name__ == "__main__":
    main()
