from fastapi import Request
from slowapi import Limiter

from config import get_settings


def client_ip(request: Request) -> str:
    settings = get_settings()
    behind_proxy = settings.trust_proxy or settings.app_env == "production"
    if behind_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
        real_ip = request.headers.get("x-real-ip", "")
        if real_ip:
            return real_ip.strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip, default_limits=["60/minute"])
