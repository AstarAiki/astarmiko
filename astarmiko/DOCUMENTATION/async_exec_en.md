AktivkaAsync class - child of Aktivka class from base.py
only two functions for massive executing: execute_on_devices and setconfig_on_devices

🚀 Benefits:

    Connection and command execution on devices happen in parallel.

    Improved performance when working with a large number of devices.

    Uses asyncio.gather().

🖥️ Example launch:
bash

python async_exec.py

It will execute:

    show version on the specified devices.

    Configuration: interface lo1, description Test.

=== Usage Example ===
python

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
