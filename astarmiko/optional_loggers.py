# optional_loggers.py

def forward_log_entry(entry: dict, rsyslog=False, loki=False, elastic=False):
    if rsyslog:
        _send_to_rsyslog(entry)
    if loki:
        _send_to_loki(entry)
    if elastic:
        _send_to_elasticsearch(entry)

def _send_to_rsyslog(entry):
    import logging.handlers
    syslog = logging.handlers.SysLogHandler(address='/dev/log')
    msg = f"{entry['device']} {entry['level']}: {entry['message']}"
    syslog.emit(logging.LogRecord("rsyslog", logging.INFO, "", 0, msg, None, None))
    syslog.close()

def _send_to_loki(entry):
    # Пример реализации отправки в Grafana Loki через HTTP
    import requests
    import time
    payload = {
        "streams": [{
            "labels": f"{{device=\"{entry['device']}\",level=\"{entry['level']}\"}}",
            "entries": [{
                "ts": f"{int(time.time())}000000000",
                "line": entry['message']
            }]
        }]
    }
    try:
        requests.post("http://localhost:3100/loki/api/v1/push", json=payload, timeout=2)
    except Exception:
        pass

def _send_to_elasticsearch(entry):
    # Пример отправки в Elasticsearch (если у тебя установлен и настроен)
    import requests
    try:
        requests.post("http://localhost:9200/logs/_doc", json=entry, timeout=2)
    except Exception:
        pass

