# manage.py
import argparse
import base
from base import Activka, setup_config

def debug_logger(func):
    """
    Декоратор, который отслеживает все точки выхода из функции.
    """
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"DEBUG: Вызов функции {func.__name__}")
        print(f"DEBUG: Входные аргументы - args: {args}, kwargs: {kwargs}")

        try:
            result = func(*args, **kwargs)
            print(f"DEBUG: Функция {func.__name__} вернула (нормальный выход): {result}")
            return result
        except Exception as e:
            print(f"DEBUG: Функция {func.__name__} вышла с исключением: {e}")
            raise
    return wrapper

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
    if not args.device[0].isalpha():
        args.device = a.by_ip[args.device]
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
