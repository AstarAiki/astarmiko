# astarmiko

**Astarmiko** is an advanced Python toolkit for managing and automating enterprise-grade network infrastructure over SSH. It provides both synchronous and asynchronous execution models, YAML-based inventory and configuration, and deep vendor-specific handling.

---

## 🚀 Features

* ✅ Unified interface for Cisco, Huawei, and others
* ⚡ Asynchronous SSH commands execution using `asyncio`
* 🔄 Automated configuration backups
* 🧠 Intelligent MAC/IP tracing and topology resolution (FindHost)
* 📁 Structured YAML configs for devices, commands, and segments
* 📊 Logging with stdout, JSON, rsyslog, Loki, Elastic support

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

Requires Python 3.8+

---

## 📂 Project Structure

* `astarmiko/base.py` – core class `Activka` for managing devices
* `astarmiko/async_exec.py` – class `ActivkaAsync` for parallel SSH
* `astarmiko/log_config.py` – flexible logging config (JSON, stdout)
* `scripts/fh.py` – FindHost utility: locate host by IP or MAC
* `YAML/` – all inventory, command mapping and segment data
* `TEMPLATES/` – TextFSM templates for structured parsing

---

## 🚀 Recommended location for configuration files

All configuration files (YAML, TEMPLATES, example) are recommended to be stored in the user's home directory:

- **Linux/macOS:** `~/astarmiko/`
- **Windows:** `C:\\Users\\username\\astarmiko\\`

This will allow you to:
✅ Easily edit configuration files  
✅ Avoid permission issues  
✅ Use them on different operating systems without changes

Example:

```bash
mkdir -p ~/astarmiko
cp -r ./astarmiko/YAML ~/astarmiko/
cp -r ./astarmiko/TEMPLATES ~/astarmiko/
cp -r ./astarmiko/example ~/astarmiko/

---

## 🧑‍💻 Usage Examples

### Run show and config commands in parallel:

```python
from astarmiko.async_exec import ActivkaAsync, setup_config

setup_config("astarmiko.yaml")
a = ActivkaAsync("activka_byname.yaml")

await a.execute_on_devices(["R1", "R2"], ["show version"])
await a.setconfig_on_devices(["R1"], ["interface lo1", "description test"])
```

### Run FindHost (fh.py)

```bash
python fh.py 192.168.1.23
```

---

## 📘 YAML Config Files

### activka\_byname.yaml

Defines all devices, their types, IPs, segment and role:

```yaml
Router1:
  device_type: cisco_ios
  ip: 10.1.1.1
LEVEL:
  Router1: R
SEGMENT:
  Router1: SEG A
```

### astarmiko.yaml

Global configuration for templates, logging, credentials, etc.

* `templpath`: path to FSM templates
* `logging`: enable/disable logging
* `add_account`: fallback credentials list

### commands.yaml

Maps vendor-agnostic command names to real CLI syntax:

```yaml
commands:
  arp_table:
    cisco_ios: "show ip arp"
    huawei: "display arp"
```

Also defines MAC formatting rules for each platform.

---

## 📚 Documentation

See full documentation in `/DOCUMENTATION` folder:

* `base_ru.md`, `async_exec_en.md`, `log_config_ru.md`, etc.

---

## 🙌 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## 🛡 License

MIT License — see `LICENSE` file.

---

Made with ❤️ by [astaraiki](https://github.com/astaraiki)

