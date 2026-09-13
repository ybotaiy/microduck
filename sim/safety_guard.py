"""Small, deterministic motion veto used independently of visual control."""
import math


class MotionGuard:
    """Latch zero commands after a terminal simulated safety event."""

    def __init__(self):
        self.reason = None

    def command(self, forward, yaw, *, fell=False, manual_stop=False,
                stale_camera=False, finite=True):
        if self.reason is None:
            if manual_stop:
                self.reason = 'MANUAL_STOP'
            elif fell:
                self.reason = 'FALL'
            elif stale_camera:
                self.reason = 'STALE_CAMERA'
            elif not finite or not (math.isfinite(forward) and math.isfinite(yaw)):
                self.reason = 'NONFINITE_COMMAND'
        if self.reason is not None:
            return 0.0, 0.0, self.reason
        return forward, yaw, None
