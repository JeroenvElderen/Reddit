"""
Timezone helpers.
"""

try:
    from zoneinfo import ZoneInfo
except Exception:
    from backports.zoneinfo import ZoneInfo

from app.config import TZ_NAME

def current_tz() -> ZoneInfo:
    return ZoneInfo(TZ_NAME)
