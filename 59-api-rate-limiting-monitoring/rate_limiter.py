"""
Sliding Window Rate Limiter.
Tracks request timestamps within a moving time window to enforce per-key rate limits.
"""
import time
import threading
from collections import deque
from typing import Dict, Tuple


class SlidingWindowRateLimiter:
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._history: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def check_and_record(self, key: str, max_requests: int) -> Tuple[bool, int, int]:
        """
        Check if request is allowed and record it if permitted.
        Returns:
            Tuple[bool, int, int]:
              - is_allowed: True if request permitted, False if rate limited.
              - remaining: Number of remaining allowed requests in current window.
              - retry_after: Seconds until the oldest request leaves window (0 if allowed).
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            if key not in self._history:
                self._history[key] = deque()

            q = self._history[key]

            # Evict timestamps outside the window
            while q and q[0] <= window_start:
                q.popleft()

            # Check limit
            if len(q) >= max_requests:
                # Earliest timestamp in current window
                oldest_timestamp = q[0]
                retry_after = max(1, int((oldest_timestamp + self.window_seconds) - now))
                return False, 0, retry_after

            # Record current request
            q.append(now)
            remaining = max(0, max_requests - len(q))
            return True, remaining, 0

    def reset_key(self, key: str):
        """Clear rate limit history for a specific key."""
        with self._lock:
            if key in self._history:
                self._history[key].clear()

    def clear(self):
        """Clear all rate limit histories."""
        with self._lock:
            self._history.clear()
