# log_config.py
from astarconf import AstarConf
import logging
import logging.handlers
import json


def get_log_config(path="log_config.yml"):
    conf = AstarConf(path)
    logconf = conf.get("log", {})
    return {
        "format": logconf.get("format", "json"),
        "stdout": logconf.get("stdout", True),
        "rsyslog": logconf.get("rsyslog", {}).get("enabled", False),
        "rsyslog_addr": logconf.get("rsyslog", {}).get("address", "/dev/log"),
        "loki": logconf.get("loki", {}).get("enabled", False),
        "loki_url": logconf.get("loki", {}).get("url", "http://localhost:3100/loki/api/v1/push"),
        "elastic": logconf.get("elasticsearch", {}).get("enabled", False),
        "elastic_url": logconf.get("elasticsearch", {}).get("url", "http://localhost:9200"),
        "elastic_index": logconf.get("elasticsearch", {}).get("index", "logs")
    }


def setup_logging(logcfg):
    handlers = []

    if logcfg["stdout"]:
        stream_handler = logging.StreamHandler()
        if logcfg["format"] == "json":
            stream_handler.setFormatter(JsonLogFormatter())
        else:
            stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        handlers.append(stream_handler)

    logging.basicConfig(level=logging.INFO, handlers=handlers)


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(log_entry, ensure_ascii=False)


# можно вызывать setup_logging(get_log_config()) при старте программы

