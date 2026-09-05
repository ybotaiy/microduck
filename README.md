# MicroDuck pet agent

A personal experiment in an expressive robot pet, developed before the Microduck hardware arrives.

Start with [PROJECT.md](PROJECT.md) for the project context, decisions, references, current state, and prioritized next steps.

The first approach is an agent on a computer that chooses and times a small catalogue of existing movement routines. The robot keeps its local movement and balance controller. Development begins with synthetic events and logs, then a simulator adapter, camera/perception, and eventually hardware.

## Repository scope

This repository contains the personal agent layer and project notes. It is private as of September 5, 2026 and was audited for public release that day; see the status line in `PROJECT.md`. No application implementation has been added yet.

Public codebases already downloaded locally remain separate and are excluded from this repository:

| Local directory | Role |
| --- | --- |
| `microduck-lab/` | [Community CPU training harness and browser viewer](https://github.com/jonathanhawkins/microduck-lab) |
| `microduck-lab/microduck/` | [Official onboard robot software](https://github.com/pollen-robotics/microduck) |
| `microduck-lab/microduck_rl/` | [Official simulation models and training tools](https://github.com/pollen-robotics/microduck_rl) |

These checkouts are local dependencies/reference material, not forks, vendored copies, or submodules of this project. Their runtime behavior has not been tested in this task. A fresh clone of the personal repository will not contain them; reproducible dependency setup is future work.

Keep `PROJECT.md` current as decisions, verified capabilities, progress, and next steps change.
