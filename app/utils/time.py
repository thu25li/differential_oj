from datetime import datetime,timezone
def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def ensure_z_suffix(dt_str: str) -> str:
    if not dt_str:
        return dt_str
    if dt_str.endswith("Z"):
        return dt_str
    return dt_str + "Z"