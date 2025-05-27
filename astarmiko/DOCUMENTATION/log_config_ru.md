📋 Что умеет log_config.py:
✅ get_log_config(path)

    Загружает параметры логирования из log_config.yml.

✅ setup_logging(logcfg)

    Настраивает logging:

        Формат: json или text

        Поток вывода: stdout включается/выключается

        Можно расширить для записи в файл или кастомных обработчиков

✅ JsonLogFormatter

    Красиво форматирует логи как JSON, например:

{"time": "2025-04-22 16:44:51,392", "level": "INFO", "message": "Команды успешно выполнены"}

🚀 Как использовать

В async_exec.py или main.py:


from log_config import get_log_config

logcfg = get_log_config()
a = ActivkaAsync("activka_byname.yaml")

await a.execute_on_devices(devices, show_cmds,
                           rsyslog=logcfg["rsyslog"],
                           loki=logcfg["loki"],
                           elastic=logcfg["elastic"])
