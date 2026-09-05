# MicroDuck pet project: context, decisions, and next steps

Last updated: September 5, 2026.

Status: planning. This is the owner's independent personal project, kept separate from the downloaded public robot/simulator projects. The personal GitHub repository must remain private.

## Resume here

The owner is a professional software engineer learning robotics. They have preordered Pollen Robotics/Hugging Face Microduck, do not yet have the hardware, and want to explore an expressive virtual/physical robot pet that might be enjoyable for their dog and one-year-old daughter.

The first approach is decided: an AI agent on an external computer or server selects and times a small catalogue of pre-made movement routines using observations, recent interaction history, and owner preferences. Existing controllers execute the movements and maintain balance. The first software experiment should use synthetic events and inspectable action logs; simulation, rendered perception, and physical integration come later.

The personal project root is `/Users/yuanjia/projects/microduck`. The owner explicitly wants additional components and an agent layer, not a fork or copied history of the public projects already downloaded beneath that folder. The existing `microduck-lab/` tree remains external material and is ignored by this repository.

The authenticated GitHub account is `ybotaiy`. The owner authorized creating and pushing an independent personal repository, provided it is private. [ybotaiy/microduck](https://github.com/ybotaiy/microduck) was created and verified private, with independent history rather than a GitHub fork.

Current scope includes inspection, project documentation, and establishing the private personal repository. Application implementation, dependency installation, builds, and training remain outside the current scope. Proposed implementation steps below are a plan for subsequent discussion, not completed work.

## Purpose and what success means

This is an exploratory learning project, not a committed product specification. The owner wants to learn how robot behavior is built and see whether a small repertoire, broad pet-like goal, and memory of interactions can produce an interesting apparent character. That character would be an effect of behavior selection and presentation; it does not imply an internal emotional life.

The central question is whether actual interactions are enjoyable. Looking at the robot, barking, approaching, or interacting for longer cannot automatically be treated as enjoyment. The dog and child are different participants with different responses. Initially, use the owner's ratings, observations, and preferences to assess routines. A simulated child or dog cannot establish enjoyment for a real child or dog.

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
| Treat engagement judgments as hypotheses. | Owner feedback and interaction history provide a starting point; attention is not a reliable automatic reward for enjoyment. |
| Defer operator imitation and new physical-skill training. | The owner explicitly chose the simpler activity-selection approach first. Imitation remains a possible later direction. |

The agent may suggest missing routines or capabilities, but suggestions are proposals for development. A routine composed from already supported movements and pauses is different from a new physical skill that needs an animation, controller, reward design, or training. Neither a natural-language request nor a high-level plan guarantees that a robot can physically execute a new maneuver.

## Intended architecture

The external computer receives observations, maintains a short interaction history and preferences, and asks the high-level agent what to do next. The agent chooses a routine and its supported parameters. An execution layer checks the request against the catalogue and passes it to an adapter. The simulator or robot executes it and reports progress, completion, or failure.

The robot's movement/balance controller remains local. High-level reasoning need not run at the motor-control frequency, and the agent is not intended to generate each motor command directly.

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

The manufacturer targets first deliveries before Christmas 2026; this is not a guarantee for the owner's particular order. The press kit describes a roughly 25 cm, under-800 g robot with RK3566 compute plus an AI accelerator, 1 GB RAM, 32 GB storage, Wi-Fi/Bluetooth, a front camera, two IMUs, and an 8×8 time-of-flight depth sensor. Camera resolution/FOV, some other specifications, and the age recommendation remain provisional. No suitability for a one-year-old has been established. [Official press kit](https://pollen-robotics.com/microduck/press-kit/)

The onboard repository documents a 50 Hz controller and camera streaming over WebRTC. The developer cheat sheet describes controlling the robot from a laptop through a Unix socket forwarded over SSH. These documents support exploring an external high-level agent, but they do not demonstrate this project's complete perception-to-action loop. [Onboard software](https://github.com/pollen-robotics/microduck), [developer cheat sheet](https://github.com/pollen-robotics/microduck/blob/main/docs/robot/cheatsheet-dev.md)

The current press kit lists 15 motors, while the locomotion policy interface described below has 14 action outputs. Do not infer the total physical motor count from a policy tensor or older local documentation; confirm the relevant model and joint mapping when building an adapter. [Press kit](https://pollen-robotics.com/microduck/press-kit/), [simulator interface](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md)

### Simulation

The official browser simulator runs MuJoCo compiled to WebAssembly and ONNX policies locally in the browser. It offers keyboard/gamepad control with a ball and arena. Its documented policy interface uses body state, joint positions/velocities, previous actions, and commands: 61 observation values and 14 position targets. Camera pixels are not the locomotion policy's input. [Open simulator](https://huggingface.co/spaces/pollen-robotics/microduck-simulator), [simulator README](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md)

The official `microduck_rl` repository documents CPU MuJoCo execution of exported policies. Its main training stack uses CUDA through MuJoCo Warp, with a documented Hugging Face Jobs option for hosted training. Running a policy and training one have different resource requirements. [Official training and execution repository](https://github.com/pollen-robotics/microduck_rl)

MuJoCo supports model cameras attached to moving bodies, which could supply a robot-view render. This establishes a rendering capability, not a ready-made external-agent integration. [MuJoCo visualization documentation](https://mujoco.readthedocs.io/en/latest/programming/visualization.html)

We have not verified a ready-made simulator camera stream and command API matching the hardware. A virtual-camera-to-external-agent bridge is proposed custom integration. Third-person viewer captures, multiplayer pose messages, and hardware WebRTC streaming should not be mistaken for that bridge. Simulation can test movement, controller behavior, and software integration; it cannot validate genuine dog/child enjoyment.

## Current project and external checkouts

Inspection date: September 5, 2026. All three downloaded repositories were already present. No external checkout was cloned, fetched, updated, or committed in this task.

| Item | Observed state |
| --- | --- |
| Personal project root | `/Users/yuanjia/projects/microduck` |
| Personal GitHub repository | [ybotaiy/microduck](https://github.com/ybotaiy/microduck), verified `PRIVATE` and not a fork on September 5, 2026. Local `origin` points only to this personal repository. |
| Personal tracked contents | This `PROJECT.md`, a short `README.md`, root `AGENTS.md` for future context maintenance, and `.gitignore`. No application code has been added. |
| External project handling | `microduck-lab/` is ignored by the personal repository. It retains its own Git history and contains the two nested Pollen checkouts. It is not vendored or added as a submodule. |
| Account verification | GitHub CLI authenticated as `ybotaiy`. No owned MicroDuck repository resolved before setup. |
| Ruled-out project | The owner confirmed that `ybotaiy/mochi` is a completely separate project. It is excluded. Nothing was deleted from that repository. |

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
| [Mini activity selection with explicit and implicit feedback (2024)](https://link.springer.com/article/10.1007/s12369-024-01124-2) | Studies adapting activity choices using ratings and interaction feedback with 24 adult participants. Useful for thinking about preferences, not evidence for infant or dog enjoyment; its abstract does not report engagement improving simply because feedback sources were combined. |
| [MIT Tega adaptive storytelling (2019)](https://www-prod.media.mit.edu/publications/a-model-free-affective-reinforcement-learning-approach-to-personalization-of-an-autonomous-social-robot-companion-for-early-literacy-educa/) | Personalized storytelling over three months with 67 children aged 4–6. This is evidence in an older-child educational setting, not evidence for a one-year-old. |
| [LOVOT technology](https://lovot.life/en/technology/) | Combines expressive design, sensors, and machine learning. The public technology page does not expose a reproducible “fun” reward or full implementation to copy. |
| [Of Dogs and Robots: More Than Human Interactions at Play? (2026)](https://iris.unito.it/handle/2318/2140392) | A small study with six dogs and their owners reports curiosity/engagement as well as avoidance/fear. It motivates evaluating each dog's actual response, not assuming robot acceptance. |

## Prioritized proposed next steps

The personal project location and separation from external checkouts are decided, and this context document is in place. None of the application implementation milestones is complete. Discuss and authorize the smallest useful prototype before implementing it.

1. **Finish the interface inventory and choose a minimal prototype layout.** The independent private personal repository is established. Inspect applicable instructions and actual backend/viewer interfaces before choosing an integration point. Keep personal components separate from the downloaded checkouts and decide the smallest necessary layout here.
2. **Define the routine catalogue and observation/action contract.** Choose a few supported routines, inputs, parameters, transition rules, stop/cancel semantics, and result events. Separate composable existing movements from skills requiring development. Deliverable: a readable catalogue with concrete synthetic scenarios.
3. **Implement a small decision-loop prototype with synthetic events and logs.** Use a configurable agent backend and a fake executor. Exercise events such as someone appearing or a ball being on the left. Inspect choices, reasons, timing, repeated-action behavior, outcomes, and owner feedback. Deliverable: replayable scenarios without depending on a camera or robot.
4. **Connect existing simulator policies through an adapter.** Compare the official CPU runner/browser simulator and the discovered community lab as integration options. Inspect available programmatic interfaces before choosing. Deliverable: a selected catalogue action executes and returns an observable result without altering low-level policy contracts.
5. **Add a virtual camera, scene, and perception bridge.** Determine where frames come from, camera pose/settings, transport, timestamps, latency, and how detections become the same observation events. Treat hardware camera properties as provisional. Deliverable: an end-to-end simulated observation-to-action experiment, clearly distinguished from real-world validation.
6. **Collect preferences and evaluate routine selection.** Start with owner ratings and annotated interaction history. Compare choices across scenarios and repetitions. Keep observed behavior separate from inferred enjoyment; simulation evaluates decision logic only. Decide later whether simple preference rules, prompt context, or a trained selector is justified.
7. **Integrate physical hardware when it arrives.** Recheck the delivered hardware, current documentation, camera/control interfaces, routine compatibility, and manufacturer guidance. Establish controlled movement and logging before supervised interaction experiments. Compare commanded and actual movement when diagnosing discrepancies.
8. **Consider missing skills or operator imitation later.** Review the agent's proposals, identify whether composition suffices, and develop/train only the capabilities that warrant it. Operator demonstrations and imitation learning remain an optional later branch of work.

## Open questions

- Which adapter boundary and dependency/version strategy will let the personal project use the external simulation tools without forking them?
- Which agent product was meant by “AstroBot/Astro,” and what configurable interface should the prototype use?
- Which few routines should define the first experiment, and which are executable in the chosen simulator version?
- Which simulator offers the simplest programmatic integration, and what camera/command bridge must be built?
- What owner feedback and observations will count as evidence of an enjoyable interaction for each participant?
- Which final hardware specifications and APIs will ship, and what model/version mismatches exist between the current local checkouts and upstream?

## Maintenance

Update this document when project decisions, rationale, verified capabilities, uncertainties, progress, or next steps change. Root `AGENTS.md` directs future agents to read and maintain it. Keep the current state and next concrete action near the top so the owner or another AI can resume without reconstructing a conversation. Label proposed work separately from implemented and verified work, and date source checks when information can change.

Record the personal repository's verified URL and visibility as setup progresses. Keep its history separate from the downloaded public projects and preserve their documentation. Keep concise dated decision/progress notes rather than accumulating raw transcripts. Do not mark a capability complete based only on a README claim or an agent proposal; record the relevant check and its limits.

### Progress record

- **September 5, 2026:** Captured initial goals, architecture decisions, research, conceptual background, known uncertainties, and proposed milestones. Verified the account and the three existing external checkouts. The owner ruled out Mochi, clarified that the public projects are dependencies/reference material, and requested an independent private personal GitHub repository for the additional agent layer. Project documentation was moved to the personal project root and the temporary documentation edits in the community lab were removed. Created `ybotaiy/microduck`, verified it private and not a fork, and configured the personal origin. No application implementation, dependency installation, build, test run, or training occurred.
