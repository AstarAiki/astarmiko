import yaml
import asyncio
from concurrent.futures import ThreadPoolExecutor

from astarmiko.base import (
    ActivkaBackup,
    TimeMeasure,
    setup_config,
)

setup_config("confbackup.yml")
from astarmiko.base import ac


def load_tasks():
    with open(ac.localpath + "config_backup.yaml") as fyaml:
        wholedict = yaml.safe_load(fyaml)
    return [(key, item) for key in wholedict.keys() for item in wholedict[key]]


async def config_save_async(mb, what, executor):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, mb.save_config_backup, *what)


async def main():
    mb = ActivkaBackup("activka_byname.yaml", "activka_byip.yaml")
    todo = load_tasks()
    executor = ThreadPoolExecutor(max_workers=20)

    tasks = [config_save_async(mb, what, executor) for what in todo]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    with TimeMeasure():
        asyncio.run(main())

