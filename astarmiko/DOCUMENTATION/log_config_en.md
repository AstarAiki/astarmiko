📋 What log_config.py can do:
✅ get_log_config(path)

Loads logging parameters from log_config.yml.  

✅ setup_logging(logcfg)

Configures logging:  

    Format: json or text  

    Output stream: stdout can be enabled/disabled  

    Can be extended for file logging or custom handlers  

✅ JsonLogFormatter

Formats logs as JSON in a clean way, for example:  

{"time": "2025-04-22 16:44:51,392", "level": "INFO", "message": "Commands executed successfully"}

🚀 How to use

In async_exec.py or main.py:
python

from log_config import get_log_config  

logcfg = get_log_config()  
a = ActivkaAsync("activka_byname.yaml")  

await a.execute_on_devices(devices, show_cmds,  
                           rsyslog=logcfg["rsyslog"],  
                           loki=logcfg["loki"],  
                           elastic=logcfg["elastic"])  
