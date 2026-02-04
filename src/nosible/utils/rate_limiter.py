import functools
import logging
import time

from pyrate_limiter import Limiter, Rate
from pyrate_limiter.buckets.in_memory_bucket import InMemoryBucket
from pyrate_limiter.exceptions import BucketFullException, LimiterDelayException

log = logging.getLogger(__name__)


def _rate_limited(endpoint):
    """
    Decorator to throttle calls to the given endpoint
    using whatever limiters you’ve stored in self._limiters.
    """

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            # print(f"[RATE LIMIT] enforcing {endpoint}")
            for rl in self._limiters[endpoint]:
                rl.acquire()
            return fn(self, *args, **kwargs)

        return wrapper

    return deco


class RateLimiter:
    """
    Thread-safe sliding-window rate limiter via PyrateLimiter.
    """

    _GLOBAL_KEY = "nosible"

    def __init__(self, max_calls: int, period_s: float):
        """
        Initialize the RateLimiter.

        Parameters
        ----------
        max_calls : int
            Maximum number of calls allowed within each time window.
        period_s : float
            Length of the rolling window, in seconds.

        Raises
        ------
        ValueError
            If max_calls is not positive or period_s is not positive.

        Examples
        --------
        >>> rl = RateLimiter(5, 2.0)
        >>> isinstance(rl, RateLimiter)
        True
        """
        # PyrateLimiter expects interval in ms
        period_ms = int(period_s * 1000)

        # Build our bucket
        bucket = InMemoryBucket([Rate(max_calls, period_ms)])
        self._limiter = Limiter(bucket, max_delay=1000)

    def acquire(self) -> None:
        """
        Block until a slot is available under the rate limit.

        This method will block the calling thread until the number
        of calls made in the last period_s seconds is strictly
        less than max_calls.  Once a slot is free, it records
        the call and returns.

        Raises
        ------
        BucketFullException
            If the limiter is configured to never delay and the bucket is full.

        Examples
        --------
        >>> rl = RateLimiter(1, 10.0)
        >>> rl.acquire()  # first call always passes
        >>> # Second call within 10 seconds will block until the window resets
        >>> start = time.monotonic(); rl.acquire(); end = time.monotonic()
        >>> end - start >= 10.0
        True
        """
        waited = False
        while True:
            try:
                self._limiter.try_acquire(self._GLOBAL_KEY)
                if waited:
                    log.info("Resumed after wait")
                return
            except BucketFullException as exc:
                # exc.meta_info['remaining_time'] is ms until next token
                wait_ms = exc.meta_info.get("remaining_time", 0)
                wait_s = max(wait_ms / 1000.0, 0.01)

                if not waited:
                    log.info(f"Waiting on rate limit: sleeping {wait_s * 1000:.3f}s")
                    waited = True

                # Ensure at least a small sleep if rounding to zero
                time.sleep(wait_s)

    def try_acquire(self, name: str = None) -> bool:
        """
        Attempt to acquire a slot without blocking.

        Returns
        -------
        bool
            True if a slot was available and consumed; False if the
            rate limit has been reached.

        Examples
        --------
        >>> rl = RateLimiter(1, 10.0)
        >>> rl.try_acquire()
        True
        >>> # Immediately calling again will fail
        >>> rl.try_acquire()
        False
        """
        key = name if name else self._GLOBAL_KEY

        try:
            self._limiter.try_acquire(key)
            return True
        except (BucketFullException, LimiterDelayException):
            # Return False instead of crashing when the limit is hit
            return False