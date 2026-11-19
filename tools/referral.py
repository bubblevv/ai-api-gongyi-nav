from __future__ import annotations

import re
from urllib.parse import urlparse


REFERRAL_SIGNALS = ("aff=", "ref=", "invite=", "/invite/")
TELEGRAM_INVITE_HOSTS = {"t.me", "telegram.me", "telegram.dog"}
TELEGRAM_INVITE_PATTERN = re.compile(r"(?:^|[?&])start=inv_[A-Za-z0-9_]+", re.IGNORECASE)


def is_telegram_invite(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in TELEGRAM_INVITE_HOSTS and bool(TELEGRAM_INVITE_PATTERN.search(url))


def has_referral_signal(url: str) -> bool:
    lowered = url.lower()
    return any(signal in lowered for signal in REFERRAL_SIGNALS) or is_telegram_invite(url)
