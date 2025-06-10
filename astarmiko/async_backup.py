# async_backup.py
import asyncio
import aiofiles
import asyncssh
from astarmiko.base import Activka, setup_config
from typing import List, Dict, Any
import os
import re

class ActivkaBackupAsync(Activka):
    def __init__(self, byname):
        super().__init__(byname)
        self._setup_backup_servers()

    def _setup_backup_servers(self):
        self.main_backup_server = {
            'name': self.ac.main_backup_server['name'],
            'protocol': 'local',
            'local_root': self.ac.main_backup_server['local_root']
        }

    async def get_curr_config_async(self, device: str) -> List[str]:
        config = self.get_curr_config(device)
        return config if isinstance(config, list) else config.splitlines()

    async def write_backup_async(self, segment: str, filename: str, content: str):
        path = os.path.join(self.main_backup_server['local_root'], segment)
        os.makedirs(path, exist_ok=True)
        filepath = os.path.join(path, filename)
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(content)

    async def save_config_backup(self, segment: str, device: str):
        try:
            config_lines = await self.get_curr_config_async(device)
            content = '\n'.join(config_lines)
            filename = f"{device}-{self._get_timestamp()}.cfg"
            await self.write_backup_async(segment, filename, content)
            print(f"[+] Backup saved: {device} -> {filename}")
        except Exception as e:
            print(f"[!] Error backing up {device}: {e}")

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d')

# === Пример использования ===
if __name__ == '__main__':
    import yaml
    from astarmiko.base import TimeMeasure

    async def main():
        setup_config("confbackup.yml")
        from astarmiko.base import ac

        with open(ac.localpath + "config_backup.yaml") as fyaml:
            wholedict = yaml.safe_load(fyaml)

        tasks = [(key, item) for key in wholedict.keys() for item in wholedict[key]]
        mb = ActivkaBackupAsync("activka_byname.yaml", "activka_byip.yaml")

        await asyncio.gather(*(mb.save_config_backup(*what) for what in tasks))

    asyncio.run(main())

