Готово! 🔄 Я переписал обе функции (execute_on_devices и setconfig_on_devices) с использованием asyncio в классе ActivkaAsync.
🚀 Преимущества:

    Подключение и выполнение команд на устройствах — параллельно.

    Повышение производительности при работе с большим количеством устройств.

    Используется asyncio.gather().

🖥️ Пример запуска:

python async_exec.py

Он выполнит:

    show version на указанных устройствах.

    Конфигурацию: interface lo1, description Test.

# === Пример использования ===
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

