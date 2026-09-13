"""Image-only magenta-ball observations and locomotion commands.

This module deliberately imports no simulator APIs and accepts no world poses,
ball coordinates, segmentation IDs, depth images, or target schedule.
"""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class BallObservation:
    horizontal: float  # -1 image left, +1 image right
    diameter: float  # bounding-box diameter / image height
    pixels: int


def detect_ball(rgb):
    """Largest connected magenta component; return None for absent/clipped targets."""
    rgb = np.asarray(rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError('Expected HxWx3 RGB image')
    r, g, b = (rgb[:, :, i].astype(np.int16) for i in range(3))
    mask = (r > 75) & (b > 55) & (r > 1.6*g) & (b > 1.5*g)
    h, w = mask.shape
    visited = np.zeros_like(mask)
    best = []
    for y, x in zip(*np.where(mask)):
        if visited[y, x]:
            continue
        pending, component = [(int(y), int(x))], []
        visited[y, x] = True
        while pending:
            cy, cx = pending.pop()
            component.append((cy, cx))
            for ny, nx in ((cy-1,cx),(cy+1,cx),(cy,cx-1),(cy,cx+1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny,nx] and not visited[ny,nx]:
                    visited[ny,nx] = True
                    pending.append((ny,nx))
        if len(component) > len(best):
            best = component
    if len(best) < 12:
        return None
    ys, xs = np.array(best).T
    lo_x, hi_x, lo_y, hi_y = xs.min(), xs.max(), ys.min(), ys.max()
    if lo_x == 0 or hi_x == w-1 or lo_y == 0 or hi_y == h-1:
        return None
    width, height = hi_x-lo_x+1, hi_y-lo_y+1
    if len(best)/(width*height) < .35:
        return None
    return BallObservation(float(2*xs.mean()/(w-1)-1), float(max(width,height)/h),len(best))


class VisionFollower:
    stop_size = .17
    resume_size = .14
    resume_dwell = .8
    max_frame_age = .12

    def __init__(self):
        self.state = 'LOST'
        self.last_change = -math.inf
        self.events = []

    def command(self, now, frame_time, observation):
        """Commands depend only on pixels and timing; zero on missing/stale frames."""
        previous = self.state
        if observation is None or not 0 <= now-frame_time <= self.max_frame_age:
            self.state = 'LOST'
        elif observation.diameter >= self.stop_size:
            self.state = 'STOP'
        elif self.state == 'STOP':
            if observation.diameter <= self.resume_size and now-self.last_change >= self.resume_dwell:
                self.state = 'APPROACH'
        else:
            self.state = 'APPROACH'
        if self.state != previous:
            self.last_change = now
            self.events.append(dict(t=now, previous=previous, state=self.state))
        if self.state != 'APPROACH':
            return 0., 0., self.state
        # Positive world yaw is left, the opposite of image horizontal offset.
        yaw_rate = max(-1.2,min(1.2,-1.8*observation.horizontal))
        return .3, yaw_rate, self.state
