# CPU simulation experiments

The first implemented exercise reuses the official standing and walking ONNX
policies. `sim/experiment.py` imports the unmodified official inference runner,
steps MuJoCo at 200 Hz and queries the policy at 50 Hz. No training or LLM is used.

## Reproduce

From this repository root, install an isolated environment (Python 3.10 was
tested for this standalone script; this is not the full official training env):

```sh
mkdir -p microduck-lab
git clone https://github.com/pollen-robotics/microduck_rl.git microduck-lab/microduck_rl
git -C microduck-lab/microduck_rl checkout --detach 53b8971b61baf5b7f3c16d135dd7cac37623de4b
python3 -m venv microduck-lab/.venv
microduck-lab/.venv/bin/python -m pip install -r sim/requirements.txt
mkdir -p microduck-lab/policies
curl -fL https://huggingface.co/pollen-robotics/microduck-policies/resolve/main/alpha_walking.onnx -o microduck-lab/policies/alpha_walking.onnx
curl -fL https://huggingface.co/pollen-robotics/microduck-policies/resolve/main/alpha_stand.onnx -o microduck-lab/policies/alpha_stand.onnx
shasum -a 256 microduck-lab/policies/*.onnx
```

The clone commands above are for a fresh setup; reuse existing external checkouts
without overwriting local changes. Model files are now hosted on the official
[Hugging Face repository](https://huggingface.co/pollen-robotics/microduck-policies),
not in the current runtime GitHub tree. `main` is mutable: require these hashes
to reproduce the September 9 results, or label new downloads as a new experiment:

| Model | SHA-256 |
|---|---|
| alpha_walking.onnx | e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c |
| alpha_stand.onnx | 1569268713e40deea795dd2922dba50d3621e15a872855408b6b1b125b1c094b |

Run:

```sh
microduck-lab/.venv/bin/python sim/experiment.py --mode baseline --video --out runs/baseline
microduck-lab/.venv/bin/python sim/experiment.py --mode push --push 0.4 --video --out runs/push
microduck-lab/.venv/bin/python sim/experiment.py --mode ball --seconds 18 --ball 0.8 0.35 --video --out runs/ball-left
microduck-lab/.venv/bin/python sim/experiment.py --mode ball --seconds 24 --ball 0.65 -0.5 --video --out runs/ball-right
microduck-lab/.venv/bin/python sim/experiment.py --mode ball --seconds 30 --ball -0.6 0.3 --video --out runs/ball-behind
```

Omit `--video` for numerical checks without a graphics context. On macOS,
offscreen video still needs CoreGraphics access; a restricted sandbox can block
it. Outputs are `rollout.mp4`, sampled PNG frames, `trajectory.jsonl`, and
`summary.json` with source/model hashes and library versions. No paths or host
identifiers are recorded in result data. `runs/` and external dependencies are
ignored by Git.

## What the controller does

After a two-second settle, read the stationary ball's simulation coordinates and
the robot's ground-truth position and yaw. Compute the bearing error, wrap it
across ±π, and request a bounded yaw rate. The walking command is 0.3 m/s; measured
velocity is not assumed to equal that command. At 0.24 m center distance, latch
stop and request the standing policy. This is a walking turn, not an in-place turn.

In these static modes, the ball is fixed in the scene. The separate `follow` mode is documented in `DYNAMIC_FOLLOW.md`. There is no camera perception, ball following,
kick, gait training, or obstacle avoidance. For the push exercise, at three
seconds overwrite trunk planar velocity with `[0.4, 0]` m/s, following the official
runner's perturbation method. This is a velocity impulse approximation, not a
measured physical force.

## Measured results — September 9, 2026

These are deterministic single runs from one initial pose per target. They are
not a robustness estimate. Detailed records are in `sim/results/`.

| Run | Final ball-center distance (m) | Final-second mean speed (m/s) | Result |
|---|---:|---:|---|
| Baseline, 8 s | — | 0.000347 | Stable stand; max tilt 1.32° |
| Push, 8 s | — | 0.000400 | Recovered; max tilt 4.16° |
| Ball (0.8, 0.35), 18 s | 0.2063 | 0.000371 | Stopped, no fall or ball contact |
| Ball (0.65, -0.5), 24 s | 0.2448 | 0.000362 | Stopped, no fall or ball contact |
| Ball (-0.6, 0.3), 30 s | 0.2385 | 0.000471 | Stopped, no fall or ball contact |

Distance is between trunk freejoint position and ball center, not toe-to-ball
clearance. Speed is the mean planar speed over the last 50 samples (one second).
Ball success requires a latched stop, final distance 0.18–0.28 m, final-second
speed below 0.01 m/s, bearing error below 0.35 rad, and no detected fall/contact.
Fall detection uses trunk tilt above 60° or trunk height below 0.055 m; these are
experiment criteria, not a hardware safety specification. Rendered clips and
sampled frames were also inspected.

An earlier controller requested zero forward speed while turning. It stalled
for right-side and behind targets: yaw moved initially but then stopped changing.
Walking turns passed the three target runs. This is an observed command-response
limitation in this model/policy combination, not a claim that the robot can
never turn in place.

## Limits and next experiment

This version uses XML position actuators (`no BAM`), deliberately labeled on
every frame. It does not validate the default BAM actuator dynamics or real
hardware. The subsequent authorized experiment is dynamic following with ground-truth
coordinates; see `DYNAMIC_FOLLOW.md`. BAM comparison remains deferred. Random initial
poses, friction variation, stronger pushes, and noisy localization are untested.

## Attribution

The imported runner and MJCF scene are from
[pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl)
(Apache-2.0), pinned above. Initialization and perturbation conventions follow
that runner; external source is not vendored or modified. The local steering,
measurement, and rendering wrapper is part of this repository's Apache-2.0 code.
