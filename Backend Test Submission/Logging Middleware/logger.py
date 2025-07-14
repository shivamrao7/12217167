import datetime

def log_request(method, path, status, remote_addr):
    now = datetime.datetime.now().isoformat()
    log_line = f"{now} {remote_addr} {method} {path} {status}\n"
    with open("access.log", "a", encoding="utf-8") as f:
        f.write(log_line) 