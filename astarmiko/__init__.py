"""
astarmiko_async
================

Asynchronous extensions and tools for managing multi-vendor network infrastructure
using AstarMiko-style configuration and automation.

Modules:
--------
- async_exec: Parallel execution of show/config commands
- async_backup: Asynchronous configuration backup
- base: Core device management logic
- cli: Command-line interface wrapper
- log_config: Logging configuration loader
- optional_loggers: External logging (rsyslog, Loki, Elasticsearch)

Usage:
------
>>> from astarmiko_async.async_exec import ActivkaAsync
>>> a = ActivkaAsync("activka_byname.yaml")
>>> await a.execute_on_devices(["R1"], {"cisco_ios": ["show version"]})

"""

__version__ = "0.2.0"

