"""Fit a tiny local visual action model from the existing rules teacher.

The teacher and learner consume only image-derived bearing/size plus the
previous executed action.  World pose and target coordinates never enter the
model inputs or labels.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from vision_follow import BallObservation, VisionFollower


class Policy(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(4, 16), nn.Tanh(), nn.Linear(16, 16),
                                    nn.Tanh(), nn.Linear(16, 2))

    def forward(self, features):
        return self.layers(features)


def make_data(seed, episodes=600, steps=90):
    rng = np.random.default_rng(seed)
    features, labels = [], []
    for _ in range(episodes):
        teacher = VisionFollower()
        previous = np.zeros(2, dtype=np.float32)
        direction = rng.uniform(-.8, .8)
        start, nearest = rng.uniform(.035, .09), rng.uniform(.175, .205)
        for step in range(steps):
            t = step * .1
            phase = step / (steps - 1)
            if phase < .55:
                diameter = start + (nearest - start) * phase / .55
            elif phase < .72:
                diameter = nearest + rng.normal(0, .003)
            else:
                diameter = .12 + .02 * (phase - .72) / .28
            visible = not (rng.random() < .025)
            bearing = np.clip(direction + .18 * np.sin(step / 13) + rng.normal(0, .025), -.95, .95)
            observation = BallObservation(bearing, diameter, 100) if visible else None
            forward, yaw, _ = teacher.command(t, t, observation)
            if observation is not None:
                features.append([observation.horizontal, observation.diameter, *previous])
                labels.append([forward, yaw])
            previous[:] = [forward, yaw]
    return np.asarray(features, dtype=np.float32), np.asarray(labels, dtype=np.float32)


def fit(seed, epochs):
    torch.manual_seed(seed)
    x, y = make_data(seed)
    split = int(.8 * len(x))
    model = Policy()
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3)
    classifier = nn.BCEWithLogitsLoss()
    regression = nn.MSELoss()
    train_x, train_y = torch.from_numpy(x[:split]), torch.from_numpy(y[:split])
    valid_x, valid_y = torch.from_numpy(x[split:]), torch.from_numpy(y[split:])
    for _ in range(epochs):
        optimizer.zero_grad()
        prediction = model(train_x)
        move = (train_y[:, :1] > .1).float()
        moving = move[:, 0] > 0
        yaw_loss = regression(torch.tanh(prediction[moving, 1:]) * 1.2, train_y[moving, 1:])
        loss = classifier(prediction[:, :1], move) + yaw_loss
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        def metrics(features, labels):
            prediction = model(features)
            move = (labels[:, :1] > .1).float()
            accuracy = float(((prediction[:, :1] >= 0) == (move > 0)).float().mean())
            moving = move[:, 0] > 0
            yaw_mse = float(regression(torch.tanh(prediction[moving, 1:]) * 1.2, labels[moving, 1:]))
            return accuracy, yaw_mse
        train_accuracy, train_yaw_mse = metrics(train_x, train_y)
        validation_accuracy, validation_yaw_mse = metrics(valid_x, valid_y)
    return model.eval(), {'seed': seed, 'epochs': epochs, 'train_examples': len(train_x),
                          'validation_examples': len(valid_x), 'train_move_accuracy': train_accuracy,
                          'validation_move_accuracy': validation_accuracy,
                          'train_yaw_mse': train_yaw_mse,
                          'validation_yaw_mse': validation_yaw_mse,
                          'output_schema': 'move logit, raw yaw; command adapter applies sigmoid/tanh bounds'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--epochs', type=int, default=700)
    args = parser.parse_args()
    model, report = fit(args.seed, args.epochs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sample = torch.zeros((1, 4), dtype=torch.float32)
    torch.onnx.export(model, sample, str(args.out), input_names=['features'],
                      output_names=['commands'], dynamo=False)
    args.out.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
