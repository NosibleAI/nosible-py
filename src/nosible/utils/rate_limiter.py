"""Rate-limiting support for NOSIBLE client operations."""

import os
import logging
import time
from typing import Optional

from pyrate_limiter import Limiter, Rate
from pyrate_limiter.buckets.in_memory_bucket import InMemoryBucket
from pyrate_limiter.exceptions import BucketFullException, LimiterDelayException

GLOBAL_LIMITER_KEY = f"nosible-{os.getpid()}"
LOGGER = logging.getLogger(name=__name__)


class RateLimiter:
    """Thread-safe sliding-window rate limiter."""

    def __init__(
        self: "RateLimiter",
        max_calls: int,
        period_s: float
    ) -> None:
        """
        Initialise a sliding-window rate limiter.

        :param max_calls: Maximum calls allowed within the window.
        :param period_s: Window duration in seconds.
        :return: None.
        """
        if max_calls <= 0:
            raise ValueError("max_calls must be greater than zero")
        if period_s <= 0:
            raise ValueError("period_s must be greater than zero")

        period_ms = int(period_s * 1000)
        bucket = InMemoryBucket(
            rates=[
                Rate(
                    limit=max_calls,
                    interval=period_ms
                )
            ]
        )
        self.limiter = Limiter(
            argument=bucket,
            max_delay=1000
        )

    def acquire(
        self: "RateLimiter"
    ) -> None:
        """
        Block until a rate-limit slot is available.

        :return: None.
        """
        waited = False
        while True:
            try:
                self.limiter.try_acquire(name=GLOBAL_LIMITER_KEY)
                if waited:
                    LOGGER.info(msg="Resumed after rate-limit wait")
                return
            except BucketFullException as error:
                wait_ms = error.meta_info.get("remaining_time", 0)
                wait_s = max(wait_ms / 1000.0, 0.01)
                if not waited:
                    LOGGER.info(
                        msg=(
                            "Waiting on rate limit: sleeping "
                            f"{wait_s * 1000:.3f}ms"
                        )
                    )
                    waited = True
                time.sleep(wait_s)

    def try_acquire(
        self: "RateLimiter",
        name: Optional[str] = None
    ) -> bool:
        """
        Attempt to acquire a slot without blocking.

        :param name: Optional limiter identity.
        :return: Whether a slot was acquired.
        """
        key = name if name else GLOBAL_LIMITER_KEY
        try:
            self.limiter.try_acquire(name=key)
            return True
        except (BucketFullException, LimiterDelayException):
            return False
