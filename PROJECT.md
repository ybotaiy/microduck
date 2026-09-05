# MicroDuck pet project: context, decisions, and next steps

Last updated: September 5, 2026.

Status: planning, architecture refined. This is the owner's independent personal project, kept separate from the downloaded public robot/simulator projects. The GitHub repository is private as of September 5, 2026; it was audited that day for public release (no secrets, single-commit history, local paths and personal details removed) and the owner may make it public. Nothing that must stay private should be added here; use the local knowledge base for that.

## Resume here

The owner is a professional software engineer learning robotics. They have preordered Pollen Robotics/Hugging Face Microduck, do not yet have the hardware, and want to explore an expressive virtual/physical robot pet whose apparent character comes from selecting and timing existing routines.

The first approach is decided: an AI agent on an external computer or server selects and times a small catalogue of pre-made movement routines using observations, recent interaction history, and owner preferences. Existing controllers execute the movements and maintain balance. The first software experiment should use synthetic events and inspectable action logs; simulation, rendered perception, and physical integration come later.

Architecture refined on September 5, 2026 into three tiers: a slow deliberative layer (a configurable LLM backend, cloud acceptable, event-driven or roughly 0.2 to 1 Hz), a local execution layer (a small state machine that owns the robot's time, validates requests against the catalogue, plays a default routine when nothing is queued or the agent misses its deadline, and handles the stop interrupt), and the robot's existing 50 Hz controller. Decisions are asynchronous: the execution layer asks for the *next* routine while the current one plays, with a deadline. Build order for the first prototype: catalogue and contract, then the execution state machine with a fake executor, then the LLM decision function last. The build design is in `DESIGN.md`. v0.2 (September 5, 2026, awaiting review) re-scoped the project after the owner's review and a research pass over the neighbors: the centerpiece is measuring what the shipped policies physically honor, authoring routines inside that envelope, testing whether they are legible, and comparing selectors blind (random, rules, LLM); the selection loop itself is a thin, mostly imported enabler.

The personal project root is the directory containing this file. The owner explicitly wants additional components and an agent layer, not a fork or copied history of the public projects already downloaded beneath that folder. The existing `microduck-lab/` tree remains external material and is ignored by this repository.

The authenticated GitHub account is `ybotaiy`. The owner authorized creating and pushing an independent personal repository, provided it is private. [ybotaiy/microduck](https://github.com/ybotaiy/microduck) was created and verified private, with independent history rather than a GitHub fork.

Current scope includes inspection, project documentation, and establishing the private personal repository. Application implementation, dependency installation, builds, and training remain outside the current scope. Proposed implementation steps below are a plan for subsequent discussion, not completed work.

## Purpose and what success means

This is an exploratory learning project, not a committed product specification. The owner wants to learn how robot behavior is built and see whether a small repertoire, broad pet-like goal, and memory of interactions can produce an interesting apparent character. That character would be an effect of behavior selection and presentation; it does not imply an internal emotional life.

The central question is whether routines read as intended and whether the choice of routine matters, measured first in simulation and later in live interaction. Looking at the robot, approaching, or interacting for longer cannot automatically be treated as a positive response. Initially, use the owner's ratings, observations, and preferences to assess routines. A simulated participant cannot establish how a real one responds.

Before hardware arrives, success means an understandable decision loop that selects plausible routines from a bounded catalogue, records what happened, and can later connect to a simulator. It does not require training a new locomotion policy or solving visual perception immediately.

## Decisions and rationale

| Decision | Rationale and boundaries |
| --- | --- |
| Use an independent private personal repository. | Keep the owner's new agent layer and notes separate from downloaded public projects; do not fork them or copy their histories into the personal repository. |
| Start with selecting existing activities and routines. | This isolates the interesting pet-behavior question from the harder problem of developing new physical skills. |
| Run perception and the high-level agent on the owner's computer/server. | It allows experimentation with different agent backends while the robot retains its fast local control loop. |
| Keep the agent backend configurable. | The owner verbally mentioned an “AstroBot/Astro instance”; the exact product is unconfirmed. No vendor, model, or agent framework has been selected. |
| Use an explicit action catalogue and simulator/robot adapter. | Decisions can be evaluated without hardware and connected to different execution environments later. |
| Begin with synthetic events, then add camera/perception. | A scenario such as “someone appeared” or “ball on the left” can exercise the decision loop before a video pipeline exists. |
| Treat engagement judgments as hypotheses. | Owner feedback and interaction history provide a starting point; attention is not a reliable automatic reward signal. |
| Use three tiers: slow agent, local execution state machine, fast controller. | Matches how comparable systems are built (see the comparison below). The middle tier owns timing, validation, defaults, and interrupts so the agent never has to be fast. Reactive tracking and sensor reflexes are later inputs to this tier, not a redesign. |
| Make agent decisions asynchronous with a deadline and a default. | Routines last one to five seconds, so a decision for the next slot can hide a cloud round trip. A synchronous loop would bake a pause between every routine. Decision latency is logged from the first run as a first-class metric. |
| Accept a cloud LLM backend for the slow layer. | Local models on the owner's machine would land in a similar latency range with weaker reasoning. The lever for responsiveness is asynchrony and local reflexes, not model location. Google's Gemini Robotics-ER orchestrator is served through a cloud API and drives real robots the same way. |
| License the repository Apache-2.0. | Decided September 5, 2026, reversing the earlier no-license choice. Matches upstream and every borrowed neighbor, and lets the envelope tables, routine recipes, and evaluation method be reused. |
| Phase the goals; live-interaction evaluation comes last. | Decided September 5, 2026. Early phases succeed on measured envelope, legibility, validity, inspectability, and latency. How real participants respond is measured only when hardware exists. |
| Anything the official M9 brain will replace is not the main focus. | Decided September 5, 2026. Disposable layers may be built if they are cheap, but the project centers on whatever is genuinely the most interesting problem to learn in this field, decided after reviewing what already exists. |
| Keep the phased plan with a deterministic rules baseline. | Decided September 5, 2026. The rules backend is fallback, replay engine, and the comparison baseline for any learned or LLM selector. |
| Defer operator imitation and new physical-skill training. | The owner explicitly chose the simpler activity-selection approach first. Imitation remains a possible later direction. |

The agent may suggest missing routines or capabilities, but suggestions are proposals for development. A routine composed from already supported movements and pauses is different from a new physical skill that needs an animation, controller, reward design, or training. Neither a natural-language request nor a high-level plan guarantees that a robot can physically execute a new maneuver.

## Intended architecture

The external computer receives observations, maintains a short interaction history and preferences, and asks the high-level agent what to do next. The agent chooses a routine and its supported parameters. An execution layer checks the request against the catalogue and passes it to an adapter. The simulator or robot executes it and reports progress, completion, or failure.

The robot's movement/balance controller remains local. High-level reasoning need not run at the motor-control frequency, and the agent is not intended to generate each motor command directly.

The execution layer sits between them and is built first. In the synthetic-event stage it is a single state machine holding the current routine and its remaining duration, validating requests, playing a default routine on idle or missed deadline, and accepting a stop interrupt. Later additions to the same component, in order: reactive tracking driven by perception at 5 to 10 Hz (head follows a ball or person), sensor reflexes (fall detection, depth-sensor halt), and behavior blending. Disney's animation engine for the BDX droids is the reference shape: background loops, triggered clips, and joystick-modulated poses above one RL policy. The agent in this project only triggers clips.

### Comparable systems (checked September 5, 2026)

Every advanced system checked is layered by rate. They differ in what passes between layers. Language and explicit commands are as common at the frontier as learned latents, and the explicit-command shape is the one a solo developer without robot training data can build.

| System | Slow layer | Fast layer | Message between layers | Source |
| --- | --- | --- | --- | --- |
| Figure Helix | 7B VLM, 7 to 9 Hz | 80M policy, 200 Hz | Continuous latent vector, trained end to end | [Figure](https://www.figure.ai/news/helix) |
| NVIDIA GR00T N1 | VLM, 10 Hz | Diffusion transformer, 120 Hz | Token embeddings via cross-attention, jointly trained | [arXiv](https://arxiv.org/html/2503.14734) |
| Physical Intelligence π0.5 | Same backbone predicts a subtask in language | 300M action expert, one-second chunks | Language | [π0.5](https://www.pi.website/blog/pi05) |
| Gemini Robotics 1.5 | ER 1.5 orchestrator via cloud API | VLA 1.5 on the robot | Natural-language instruction per step | [DeepMind](https://deepmind.google/blog/gemini-robotics-15-brings-ai-agents-into-the-physical-world/) |
| Boston Dynamics Atlas with TRI | 450M diffusion policy, 30 Hz | Existing MPC controller | Position targets over the teleoperation interface | [Boston Dynamics](https://bostondynamics.com/blog/large-behavior-models-atlas-find-new-footing/) |
| Disney BDX droid | Animation engine fed by remote control and clips | RL policies at 50 Hz, actuators at 600 Hz | Explicit commands: head pose, 2D velocity, turn rate | [arXiv](https://arxiv.org/html/2501.05204v1) |

This project's design is closest to Disney's. The Disney command signals (velocity, turn rate, head pose) are the same kind of command vector the Microduck walking policy consumes. Choosing routines with an LLM is the language-interface pattern used by π0.5 and Gemini Robotics.

The following contract is a design proposal, not an existing interface:

| Element | Initial content to define |
| --- | --- |
| Observation | Timestamp, event type, source (synthetic, rendered perception, or hardware), relevant object/participant information, and uncertainty. |
| Interaction context | Recent events, selected routines, outcomes, repetition history, and owner feedback/preferences. |
| Action | Catalogue routine identifier, allowed parameters, requested duration, and a short reason for inspection. |
| Catalogue entry | What the routine does, prerequisites, parameter bounds, expected completion, interruptibility, and availability in each environment. |
| Execution result | Accepted/rejected, running/completed/interrupted/failed, timestamps, and relevant robot/simulator state. |
| Adapter | Translate the agreed actions into the selected simulator or robot interface, while exposing consistent results. |

Candidate early routines could include looking in a direction, a brief walk/turn, sitting/standing, a greeting composed from supported movements, and waiting. These are examples to investigate, not a verified executable catalogue. Exact capabilities, command semantics, transitions, and a reliable stop/cancel path need inspection before implementation.

Start on the home network. The documented laptop-control path does not establish that remote internet access will work without additional network configuration.

## Verified platform context and limits

These facts were checked against official documentation on September 5, 2026. They describe published capabilities, not hardware tested by the owner. Recheck changing specifications and interfaces before integrating them.

### Hardware and onboard software

The manufacturer targets first deliveries before Christmas 2026; this is not a guarantee for the owner's particular order. The press kit describes a roughly 25 cm, under-800 g robot with RK3566 compute plus an AI accelerator, 1 GB RAM, 32 GB storage, Wi-Fi/Bluetooth, a front camera, two IMUs, and an 8×8 time-of-flight depth sensor. Camera resolution/FOV, some other specifications, and the age recommendation remain provisional. [Official press kit](https://pollen-robotics.com/microduck/press-kit/)

The onboard repository documents a 50 Hz controller and camera streaming over WebRTC. The developer cheat sheet describes controlling the robot from a laptop through a Unix socket forwarded over SSH. These documents support exploring an external high-level agent, but they do not demonstrate this project's complete perception-to-action loop. [Onboard software](https://github.com/pollen-robotics/microduck), [developer cheat sheet](https://github.com/pollen-robotics/microduck/blob/main/docs/robot/cheatsheet-dev.md)

The current press kit lists 15 motors, while the locomotion policy interface described below has 14 action outputs. Do not infer the total physical motor count from a policy tensor or older local documentation; confirm the relevant model and joint mapping when building an adapter. [Press kit](https://pollen-robotics.com/microduck/press-kit/), [simulator interface](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md)

### Behaviors the platform already exposes (inspected September 5, 2026)

Read from the local official checkout (`duck-ipc-proto`, `robotd`, `robotctl`, `policies/README.md`, `docs/ideas/autonomous_behavior.md`, `docs/project/roadmap.md`). Not run.

| Layer | What exists | Count |
| --- | --- | --- |
| Shipped ONNX policies | walking, stand with body pose, sit/stand, ground pick, kick left, kick right, roller, roller crouch, roulade. All 61-observation, 14-action. `robotd` picks the net by a priority chain: roulade > kick > ground pick > sit/rise > stand > walk. | 9 |
| Continuous command channels | `robot.move` (vx, vy, yaw rate), `robot.head` (neck pitch, head pitch, head yaw, head roll), body pose (z, roll, pitch), `robot.look`. These are the 13-value command block in the observation. | 3 to 4 |
| One-shot skills (`Skill` enum) | ground pick (~3 s), kick left, kick right (~0.5 s, blind to the ball), sit toggle, roulade (~1 s, chainable). | 5 |
| Sounds (`SoundTag` enum) | alarm, greet, inquire, peck, chirp, coo, wheee. Voice bank is generated per robot. Mouth is a separate channel. | 7 |
| Modes | chorale (multi-duck singing over BLE), theremin (depth sensor as instrument). Bench scaffolding, opt-in. | 2 |

The prototype runtime (`apirrone/microduck_runtime`, now not publicly reachable; a public mirror holds only a README) had a 16-state autonomous brain: Chill, LookAround, Wander, TurnInPlace, Zoomies, Startle, Stretch, Ruffle, Preen, Sneeze, Dance, GroundPick, Nap, BallPlay, Petted, Held, driven by an energy/mood model, a novelty grid for wandering, depth-sensor obstacle avoidance, sound reactions, and petting detection. The official daemon has not ported it. Roadmap milestone M9, "The autonomous brain," says it "gets a design doc before it gets code," and the ideas file argues presence, mood, and beat should be inputs to one brain rather than modes beside it. The state names are documented; the recipes behind them (which commands make a Preen) are not available to this project and would have to be re-authored.

Community prior art found the same day, both Apache-2.0: `agentculture/microduck-cli` (JSON-RPC over a socket, a 50 Hz rules and arbitration tick, simulation and fake bodies only, states it "has never driven a real duck") and `shaibuafeez/microduck-ai-world` (an asynchronous vision-language brain over an OpenAI-compatible endpoint that proposes intents such as velocity, search, sit, kick, or pick, with a local wander fallback when offline). The second is close to this project's architecture and should be read before building.

Official roadmap (`docs/project/roadmap.md`, rewritten August 26, 2026) and architecture (`docs/design/architecture.md`), as read the same day: M1 to M4 done (walks, over-the-air updates, recovery net). M5 in progress: camera and WebRTC on the LAN work; the SDK and outside-LAN access are open. M8, policies from the Hugging Face Hub, is next. M9, the brain, is last, "later, deliberately," with no date, and it is a port of the prototype's on-robot state machine into the daemon or a sibling service on the robot. The architecture already reserves a place for this project: section 5.3 says a server-side LLM agent should use a WebSocket, fetch a JPEG frame every second or two, and send intents, because "LLM latency (hundreds of ms to seconds) means the agent is a high-level controller" while "reactive control stays local in robotd." That client does not exist yet. Section 6 requires a deadman (the robot stops when commands stop), intents rather than motor writes, and explicit authority arbitration between the gamepad, app, remote peer, and the autonomous layer, with local preempting remote; the priority order is open question 3. Whether the brain is part of `robotd` or its own service is open question 5.

Verified the same day, after the research pass: the local official checkout is API version 17 (commit of September 2) while upstream main is version 23 (September 3) and adds `robot.policies`, `robot.loadPolicy`, and `robot.skills`, so every neighbor's client, and this project's, is behind a moving protocol. The official training config caps head commands at ±1.10 rad (neck and head pitch), ±1.40 rad (head yaw), and ±0.31 rad (head roll), but those are curriculum ceilings; the initial ranges are ±0.05, ±0.05, ±0.07, and ±0.015 rad, and what a shipped policy honors is unmeasured. The official CPU runner (`microduck_rl/scripts/infer_policy.py`) loads all nine policies by path and exposes a 4-value head offset, a body-pose mode, and a velocity setter, which makes CPU simulation phase 1 infrastructure. Petting detection is already in the daemon (`pet-detect` crate; it coos locally) and is not in the telemetry struct. The press kit lists "Game controller, playable before writing any code, plus autonomous behaviours at launch" in the box, a 2,600 mAh battery with about one hour of runtime, two NFC antennas, and says SDK languages are still being finalised; no staff comment in the launch discussion thread clarifies the autonomy or shell access. Prototype lineage: `apirrone/microduck_runtime` is not publicly reachable; `apirrone/microduck_sounds` and `apirrone/microduck_pet_detect` are public without a license; `apirrone/Open_Duck_Mini` is Apache-2.0. The official ideas file marks the prototype's Held state as depending on deprecated pickup detection.

Verified landscape: 2 neighbors reviewed at source level and 18 more surfaced and independently verified, none refuted; the selection-loop shape exists at least eight times; none of the 20 has measured the command envelope, authored in-envelope routines, tested legibility, compared selectors blind, or run on a real duck. The table with licenses and what is borrowed is `DESIGN.md` appendix A and B.

Implication for the catalogue, now decided in `DESIGN.md` v0.2 (pending approval): the vocabulary probably should not be invented. The 16 prototype states plus the 5 skills and 7 sounds are the natural catalogue, and this project's routines would be scripted compositions of the command channels, skills, and sounds above. The agent layer's contribution is selection, timing, and memory, either as the slow layer above the official brain when M9 lands or as a stand-in for it before then.

### Simulation

The official browser simulator runs MuJoCo compiled to WebAssembly and ONNX policies locally in the browser. It offers keyboard/gamepad control with a ball and arena. Its documented policy interface uses body state, joint positions/velocities, previous actions, and commands: 61 observation values and 14 position targets. Camera pixels are not the locomotion policy's input. [Open simulator](https://huggingface.co/spaces/pollen-robotics/microduck-simulator), [simulator README](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md)

The official `microduck_rl` repository documents CPU MuJoCo execution of exported policies. Its main training stack uses CUDA through MuJoCo Warp, with a documented Hugging Face Jobs option for hosted training. Running a policy and training one have different resource requirements. [Official training and execution repository](https://github.com/pollen-robotics/microduck_rl)

MuJoCo supports model cameras attached to moving bodies, which could supply a robot-view render. This establishes a rendering capability, not a ready-made external-agent integration. [MuJoCo visualization documentation](https://mujoco.readthedocs.io/en/latest/programming/visualization.html)

We have not verified a ready-made simulator camera stream and command API matching the hardware. A virtual-camera-to-external-agent bridge is proposed custom integration. Third-person viewer captures, multiplayer pose messages, and hardware WebRTC streaming should not be mistaken for that bridge. Simulation can test movement, controller behavior, and software integration; it cannot validate how real participants respond.

## Current project and external checkouts

Inspection date: September 5, 2026. All three downloaded repositories were already present. No external checkout was cloned, fetched, updated, or committed in this task.

| Item | Observed state |
| --- | --- |
| Personal project root | The directory containing this file (the `microduck` checkout). |
| Personal GitHub repository | [ybotaiy/microduck](https://github.com/ybotaiy/microduck), verified `PRIVATE` and not a fork on September 5, 2026. Local `origin` points only to this personal repository. |
| Personal tracked contents | This `PROJECT.md`, a short `README.md`, root `AGENTS.md` for future context maintenance, and `.gitignore`. No application code has been added. |
| External project handling | `microduck-lab/` is ignored by the personal repository. It retains its own Git history and contains the two nested Pollen checkouts. It is not vendored or added as a submodule. |
| Account verification | GitHub CLI authenticated as `ybotaiy`. No owned MicroDuck repository resolved before setup. |

The downloaded codebases have different roles:

| Local path, relative to the personal project root | Verified origin and local state | Purpose |
| --- | --- | --- |
| `microduck-lab/` | [jonathanhawkins/microduck-lab](https://github.com/jonathanhawkins/microduck-lab), `main`, clean before this task; local commit `e2f7d60`. | Community CPU training/prototyping harness and browser viewer. It is not the owner's personal agent application. |
| `microduck-lab/microduck/` | [pollen-robotics/microduck](https://github.com/pollen-robotics/microduck), clean `main` tracking `origin/main`. | Official onboard control, runtime, policies, and robot documentation. |
| `microduck-lab/microduck_rl/` | [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl), clean `develop` tracking `origin/develop`. | Official training environments, robot models, and sim-to-real tooling. |

Local statuses showed no ahead/behind difference against their existing tracking refs. Because no fetch occurred, current upstream freshness is unknown.

Within the community lab, `microduck_local/` contains a Python CPU MuJoCo/Stable Baselines 3 PPO harness, behavior recipes, ONNX export/evaluation, rollout rendering, and the `duck-lab` streaming backend. Source files include `contract.py`, `walk_env.py`, `motion.py`, and `viz_server.py`; tests and example motion clips exist. Its `duck-viewer/` contains a Next.js/TypeScript/react-three-fiber viewer with policy, teach, animation, and capture panels. These are possible integration points to inspect, not proof that the desired agent API already exists.

The lab README describes its teach panel as matching requests to built-in behavior recipes, without an LLM in that loop. It describes Hugging Face token storage but says its viewer's GPU-job launcher is not wired up. That is separate from the official training repository's documented Jobs support. Nothing was run or independently benchmarked in this task.

The community lab's root README and `AGENTS.md` were read. Before changing a component in any external checkout, read its applicable instructions, including the more specific `microduck_local/AGENTS.md`, `duck-viewer/AGENTS.md`, and instructions inside each Pollen repository. The lab emphasizes preserving the shared policy contract, exporting ONNX with normalization, visually inspecting trained behavior, and treating local training as prototyping before official sim-to-real retraining.

The owner wants new functionality in this personal project rather than edits to those external projects as the starting point. Determine an adapter boundary before changing any dependency. Only this project's own files should be committed here; the public checkouts should keep their own separate histories.

## Learning concepts already discussed

- A **policy** maps observations to actions. The high-level routine selector and a fast joint-control policy solve different problems, even if both can be called policies.
- A **reward** expresses desirable outcomes during reinforcement learning; the optimizer's **loss** is the mathematical training objective used to adjust model parameters. Reward and loss are related but not interchangeable.
- Existing movement policies can be reused without training a new one. Routine composition, timing, prompts, preference storage, and software adapters do not inherently require RL.
- **Sim-to-real gap** means the simulated and physical systems differ. Command, joint, tilt, and timing logs plus controlled comparisons can help diagnose whether a failure comes from execution, sensing, timing, or an inaccurate physical model.
- **System identification** fits simulator parameters to measured behavior. MuJoCo provides tooling for comparing simulated and recorded sensor data while optimizing model parameters. This requires appropriate recorded data; collecting logs alone does not calibrate a simulator. [MuJoCo system identification](https://github.com/google-deepmind/mujoco/blob/main/python/mujoco/sysid/README.md)
- **Domain randomization** varies physical parameters, conditions, and perturbations during training to seek robustness across uncertainty. It is distinct from fitting one best model. [NVIDIA simulation-to-reality guidance](https://docs.nvidia.com/learning/physical-ai/getting-started-with-isaac-lab/latest/transferring-robot-learning-policies-from-simulation-to-reality/03-bridging-the-gap-simulation-enhancement/index.html)
- Saving interaction history may inform the next agent decision. It does not itself retrain a deployed neural policy. Any learning/update mechanism must be deliberately designed, evaluated, and recorded.

## Research references and what they do not establish

These are ideas and evidence to revisit, not a ready-made recipe or proof that this particular pet concept will work.

| Reference | Relevant idea and limit |
| --- | --- |
| [Disney, Autonomous Human-Robot Interaction via Operator Imitation (2025)](https://la.disneyresearch.com/publication/autonomous-human-robot-interaction-via-operator-imitation/) | Learns social interactions from expert operator recordings, including commands and human/robot pose. A possible later direction if demonstrations become valuable; it is not the selected first approach. |
| [Mini activity selection with explicit and implicit feedback (2024)](https://link.springer.com/article/10.1007/s12369-024-01124-2) | Studies adapting activity choices using ratings and interaction feedback with 24 adult participants. Useful for thinking about preferences, evidence from adult participants only; its abstract does not report engagement improving simply because feedback sources were combined. |
| [MIT Tega adaptive storytelling (2019)](https://www-prod.media.mit.edu/publications/a-model-free-affective-reinforcement-learning-approach-to-personalization-of-an-autonomous-social-robot-companion-for-early-literacy-educa/) | Personalized storytelling over three months with 67 children aged 4–6. This is evidence in a child educational setting, not a general result. |
| [LOVOT technology](https://lovot.life/en/technology/) | Combines expressive design, sensors, and machine learning. The public technology page does not expose a reproducible “fun” reward or full implementation to copy. |
| [Of Dogs and Robots: More Than Human Interactions at Play? (2026)](https://iris.unito.it/handle/2318/2140392) | A small study with six dogs and their owners reports curiosity/engagement as well as avoidance/fear. It motivates evaluating each animal's actual response rather than assuming robot acceptance. |

## Prioritized proposed next steps

The personal project location and separation from external checkouts are decided, and this context document is in place. None of the application implementation milestones is complete. Discuss and authorize the smallest useful prototype before implementing it.

1. **P0, contracts.** Approve `DESIGN.md` v0.2 (decisions U1 to U13); write the catalogue and event schemas, the API skew table against upstream HEAD, and the envelope protocol. One session.
2. **P1, gestures and envelope, interleaved.** For each of six table-top routines in turn: measure the channels it needs under the standing policy in CPU MuJoCo through the official runner, author it inside that envelope, render a clip. Three to four sessions; every session ends with a clip. A narrow honored range is a finding.
3. **P2, consolidation and legibility.** Complete the envelope tables (remaining channels, walking policy, both actuator models) and run the blind legibility test on the six clips with two raters. One session.
4. **P3, loop.** Thin execution layer, fake and sim adapters, random and rules backends, console, log, replay, bring-up kit against the fake daemon; mostly imported from `agentculture/microduck-cli`. One to two sessions.
5. **P4, experiment.** Claude backend and the three-arm blind comparison. One session plus API spend.

Steps 4 to 8 below are unchanged in intent and now map to P5 and P6 in `DESIGN.md`.
4. **Connect existing simulator policies through an adapter.** Compare the official CPU runner/browser simulator and the discovered community lab as integration options. Inspect available programmatic interfaces before choosing. Deliverable: a selected catalogue action executes and returns an observable result without altering low-level policy contracts.
5. **Add a virtual camera, scene, and perception bridge.** Determine where frames come from, camera pose/settings, transport, timestamps, latency, and how detections become the same observation events. Treat hardware camera properties as provisional. Deliverable: an end-to-end simulated observation-to-action experiment, clearly distinguished from real-world validation.
6. **Collect preferences and evaluate routine selection.** Start with owner ratings and annotated interaction history. Compare choices across scenarios and repetitions. Keep observed behavior separate from inferred response quality; simulation evaluates decision logic only. Decide later whether simple preference rules, prompt context, or a trained selector is justified.
7. **Integrate physical hardware when it arrives.** Recheck the delivered hardware, current documentation, camera/control interfaces, routine compatibility, and manufacturer guidance. Establish controlled movement and logging before supervised interaction experiments. Compare commanded and actual movement when diagnosing discrepancies.
8. **Consider missing skills or operator imitation later.** Review the agent's proposals, identify whether composition suffices, and develop/train only the capabilities that warrant it. Operator demonstrations and imitation learning remain an optional later branch of work.

## Open questions

- Which adapter boundary and dependency/version strategy will let the personal project use the external simulation tools without forking them?
- Which agent product was meant by “AstroBot/Astro”? The prototype takes a configurable backend with a rules fallback, so this can stay open; a cloud LLM API is the default.
- Which few routines should define the first experiment, and which are executable in the chosen simulator version?
- Which simulator offers the simplest programmatic integration, and what camera/command bridge must be built?
- What owner feedback and observations will count as evidence that a routine reads as intended in live interaction?
- What ships as "autonomous behaviours at launch," and how an external agent yields to it (ask upstream).
- Whether a shipped consumer unit offers a shell or a socket; if not, the official WebSocket agent path is the only sanctioned off-board transport and it does not exist yet.
- Whether upstream will expose the daemon's petting detection as a telemetry event.
- Which final hardware specifications and APIs will ship, and what model/version mismatches exist between the current local checkouts and upstream?

## Maintenance

Update this document when project decisions, rationale, verified capabilities, uncertainties, progress, or next steps change. Root `AGENTS.md` directs future agents to read and maintain it. Keep the current state and next concrete action near the top so the owner or another AI can resume without reconstructing a conversation. Label proposed work separately from implemented and verified work, and date source checks when information can change.

Record the personal repository's verified URL and visibility as setup progresses. Keep its history separate from the downloaded public projects and preserve their documentation. Keep concise dated decision/progress notes rather than accumulating raw transcripts. Do not mark a capability complete based only on a README claim or an agent proposal; record the relevant check and its limits.

### Progress record

- **September 5, 2026:** Captured initial goals, architecture decisions, research, conceptual background, known uncertainties, and proposed milestones. Verified the account and the three existing external checkouts. The owner clarified that the public projects are dependencies/reference material, and requested an independent private personal GitHub repository for the additional agent layer. Project documentation was moved to the personal project root and the temporary documentation edits in the community lab were removed. Created `ybotaiy/microduck`, verified it private and not a fork, and configured the personal origin. No application implementation, dependency installation, build, test run, or training occurred.
- **September 5, 2026 (later):** Refined the architecture to three tiers with an execution state machine built before the agent, asynchronous decisions with a deadline and default, and a cloud LLM backend accepted. Checked six comparable systems against primary sources and recorded the comparison. Rewrote next steps 1 to 3 as the build order. Audited the repository for public release: no secrets, one commit, no external source; replaced absolute local paths, removed personal details and an unrelated-repository note; reworded the private-only mandate. Owner decided: no license, make public. Still no code.
- **September 5, 2026 (design review):** `DESIGN.md` v0.1 drafted. The owner decided on its counterarguments: layers that M9 will replace must not be the main focus unless they are the most interesting problem to learn; review the neighbor projects properly and search for similar work before re-scoping; keep the phased plan and rules baseline; phase the goals with live-interaction evaluation last. A multi-agent research pass (neighbor review, five-angle search, adversarial verification, three scoping proposals, two judges, a completeness critic) was started to ground the re-scope. Results to be recorded here and in a revised `DESIGN.md`.
- **September 5, 2026 (re-scope):** The research pass completed: 31 agents, 2 source-level reviews, 5 search angles, 18 candidates verified with none refuted, 3 scoping proposals, 2 judges, 1 critic. Both judges chose the same scope. `DESIGN.md` v0.2 written around it: measure the body first, author legible routines inside the envelope, compare three selectors blind, import the loop. Verified corrections to earlier notes: API drift is 17 local versus 23 upstream, not 14; head caps are curriculum ceilings; petting detection is already in the daemon; something autonomous ships at launch per the press kit. The critic's claim that Ruffle is deprecated upstream was wrong; it is Held. The owner approved the re-scope (U1), the six table-top routines first (U2), Claude deferred to P4 (U3), the three-arm design (D4), borrowing with attribution (U8), measuring on demand gesture by gesture (U14), chose Apache-2.0 (U9), and agreed to ask upstream about launch autonomy and shell access (U10, U11) the same day. Committed as design v0.2.
