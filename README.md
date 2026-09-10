# MicroDuck pet agent

A personal experiment in an expressive robot pet, developed before the Microduck hardware arrives.

**See the results:** [First simulation experiments — September 9, 2026](docs/2026-09-09-simulation.md), with five looping GIFs and a short explanation of the control loop.

Start with [PROJECT.md](PROJECT.md) for the project context, decisions, references, current state, and prioritized next steps.

Initial experiment: reuse an existing policy in simulation, observe its response to a controlled push, then turn toward a stationary ball, approach, and stop before it. The first version reads the ball position directly from simulation; it does not train a gait, use vision, or kick. See `PROJECT.md` for verification status and next steps.

The next experiment is now implemented: [dynamic following](DYNAMIC_FOLLOW.md) of a slowly moving, pausing, then departing scripted ball, with stop/resume hysteresis and ground-truth coordinates. No camera is used.

## Repository scope

This repository contains the personal agent layer and project notes. It is public; private context must remain outside this repository. A CPU simulation wrapper now implements the first experiment; see [SIMULATION.md](SIMULATION.md) for setup, runs, and measured results. Licensed under Apache-2.0 (see `LICENSE`).

External codebases remain separate and are excluded from this repository (September 9 downloaded the official RL and runtime checkouts, plus model files from the official Hugging Face set):

| Local directory | Role |
| --- | --- |
| `microduck-lab/` | [Community CPU training harness and browser viewer](https://github.com/jonathanhawkins/microduck-lab) |
| `microduck-lab/microduck/` | [Official onboard robot software](https://github.com/pollen-robotics/microduck) |
| `microduck-lab/microduck_rl/` | [Official simulation models and training tools](https://github.com/pollen-robotics/microduck_rl) |

These checkouts are local dependencies/reference material, not forks, vendored copies, or submodules of this project. The standalone CPU inference wrapper has been tested with the pinned RL checkout and downloaded ONNX files. The runtime daemons and community lab have not been run. A fresh clone does not contain dependencies; setup instructions are in `SIMULATION.md`.

Keep `PROJECT.md` current as decisions, verified capabilities, progress, and next steps change.
