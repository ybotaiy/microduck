"""Reloadable learned visual controller with the same public input boundary."""
from pathlib import Path

import numpy as np
import onnxruntime as ort


class LearnedVisionController:
    """Maps current RGB features and its prior action to bounded commands.

    Missing observations are handled by the independent stop rule here rather
    than asking the learned model to extrapolate through a sensor failure.
    """

    max_frame_age = .12
    # Search uses this as a conservative independent close-target veto while
    # aligning the body.  The learned model does not own that safety boundary.
    stop_size = .17

    def __init__(self, model_path):
        self.model_path = Path(model_path)
        self.session = ort.InferenceSession(str(self.model_path), providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.state = 'LOST'
        self.events = []
        self.previous = np.zeros(2, dtype=np.float32)

    def command(self, now, frame_time, observation):
        previous = self.state
        if observation is None or not 0 <= now-frame_time <= self.max_frame_age:
            self.state = 'LOST'
            self.previous[:] = 0
        else:
            features = np.array([[observation.horizontal, observation.diameter,
                                  self.previous[0], self.previous[1]]], dtype=np.float32)
            move_logit, raw_yaw = self.session.run(None, {self.input_name: features})[0][0]
            moving = 1.0 / (1.0 + np.exp(-move_logit)) >= .5
            self.previous[:] = [.3 if moving else 0.,
                                np.clip(np.tanh(raw_yaw) * 1.2, -1.2, 1.2) if moving else 0.]
            self.state = 'APPROACH' if moving else 'STOP'
        if self.state != previous:
            self.events.append(dict(t=now, previous=previous, state=self.state))
        return float(self.previous[0]), float(self.previous[1]), self.state
