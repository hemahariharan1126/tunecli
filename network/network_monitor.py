"""
Network Monitor — Measures internet speed and determines streaming quality tier.
"""

import speedtest
from config import QUALITY_HIGH_THRESHOLD, QUALITY_MEDIUM_THRESHOLD


class NetworkMonitor:
    def __init__(self):
        self._last_speed_mbps: float = 0.0

    def measure_speed(self) -> float:
        """
        Run a speedtest and return download speed in Mbps.
        Caches the result internally.
        """
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download_bps = st.download()
            self._last_speed_mbps = download_bps / 1_000_000
        except Exception:
            self._last_speed_mbps = 0.0
        return self._last_speed_mbps

    def get_quality(self, remeasure: bool = False) -> str:
        """
        Return a quality tier string: 'high', 'medium', or 'low'.
        Uses cached speed unless remeasure=True.
        """
        speed = self.measure_speed() if remeasure else self._last_speed_mbps
        if speed >= QUALITY_HIGH_THRESHOLD:
            return "high"
        elif speed >= QUALITY_MEDIUM_THRESHOLD:
            return "medium"
        else:
            return "low"

    @property
    def last_speed_mbps(self) -> float:
        return self._last_speed_mbps
