# MicroDuck Character Bench: design v0.2 (draft for review)

Status: **draft, not approved, no code exists.** v0.2 written September 5, 2026 after the owner's review of v0.1 and a research pass over the neighboring projects. Companion to `PROJECT.md`, which holds context, decision history, and verified platform facts; this document holds the build design.

Reading guide. Sections 1 to 4 are the high-level design to approve or reject. Sections 5 to 9 are the details, section 10 maps every detail back to a high-level decision, section 11 lists the decisions only the owner can make, and the appendices hold the verified landscape and borrowed-code tables.

Claim convention (rigor mode). Factual claims carry a basis tag: `[KNOWN]` read by me from source, docs, or an API response on September 5, 2026; `[KNOWN, agent-read]` read from source by a review agent in this session and not re-read by me; `[COMPUTED]` derived here, with the arithmetic; `[INFERRED]` deduced from stated premises; `[COMMON]` standard field knowledge; `[GUESS]` no basis. Load-bearing claims carry a confidence band. Untagged sentences are design proposals.

What changed from v0.1, in one paragraph. The owner decided that layers the official M9 brain will replace are not the focus unless they are the most interesting problem to learn, that the neighbors must be reviewed properly before re-scoping, that the phased plan with a rules baseline stays, and that live-interaction evaluation is a later phase. A research pass (two source-level neighbor reviews, a five-angle search, adversarial verification of 18 candidates with none refuted, three independent scoping proposals, two judges, and a completeness critic) found that the routine-selection loop exists at least eight times in the verified landscape and that nobody has measured what the shipped policies physically honor, authored routines inside that envelope, tested whether routines are legible, or compared selectors blind. Both judges chose the same re-scope. The centerpiece is now the body and the experiment, and the selection loop is a thin, mostly imported enabler.

---

## 1. Counterarguments first

**C1. The official brain (M9) will make the selection layer redundant.** `[KNOWN]` M9 is last in the official order of work, undated, and "gets a design doc before it gets code." Decision: such a layer must not be the main focus. Three independent scopings and both judges agreed the loop is disposable. Consequence: D6 caps the loop at one to two sessions and mostly imported code; the centerpiece moves to D3 (measure the body first) and D4 (the three-arm selector experiment).

**C2. Someone already built this.** Verified, not assumed. `[KNOWN, agent-read]` The selection-loop shape (a slow LLM or rule layer picks one action from a closed vocabulary, a validator clamps, a deterministic fallback exists, reactive control stays local) appears in microduck-ai-world twice, microduck_remote_brain, quackd, OpenCastor, Ai-Robo-Dog, wire-pod, and the official Reachy Mini conversation app; the official architecture and quackd's ADR-0003 document the tiering. `[KNOWN, agent-read]` Of the seven Microduck-specific neighbors reviewed, none has run on a real duck, none has a routine catalogue with bounds, interaction memory, owner-feedback evaluation, a legibility test, or a blind selector comparison; microduck-ai-world's robot daemon sends wire shapes its own vendored daemon rejects (three of five), and microduck-cli's engine is a 50 Hz safety-rules layer with no slow decision tier. These "nobody has" claims are scoped to the 20 projects examined (appendix A). Consequence: D2 imports microduck-cli's client, protocol table, bounds, release ordering, and human gate instead of rewriting them; D3 and 5.4 are the gap.

**C3. An LLM at half a hertz may be indistinguishable from mood rules at higher cost.** `[GUESS]` Still plausible, and the v0.1 experiment could not have shown it because it had no null arm. Consequence: D4 adds a weighted-random backend as the null baseline, and the three-arm blind comparison (random, rules, LLM) is the co-headline of the project. "Indistinguishable" is an acceptable finding.

**C4. Synthetic events cannot show how real participants respond.** Decision: phase it. Consequence: live-interaction evaluation is P6 and appears in no earlier success table.

**C5. The expressive part may not be drivable in simulation.** Corrected in both directions. `[KNOWN]` The official training config lists per-joint head caps of ±1.10 rad for neck and head pitch, ±1.40 rad for head yaw, and ±0.31 rad for head roll, but its initial command ranges are ±0.05, ±0.05, ±0.07, and ±0.015 rad, with a comment that "curriculum widens them." `[INFERRED, HIGH]` What a shipped ONNX policy honors depends on how far that curriculum ran, which the config cannot tell you. `[KNOWN]` The official CPU runner loads all nine policies by path, exposes a 4-value head offset, a body-pose mode, and a velocity setter, and needs the unified 13-value command flag. Consequence: simulation is phase 1 infrastructure, not a later milestone, and P1 measures the honored envelope instead of assuming it (D3). The lab's walk environment is the alternative for locomotion only.

**C6. Skill completion is not reported on hardware.** `[KNOWN]` `robot.do` returns accepted or a reason. `[KNOWN]` The telemetry frame carries `head[4]` and `joints[]`, so head tracking is measurable even though skill state is not. Consequence: 5.8 time-based completion labeled as belief; 5.2 uses telemetry as the hardware measurement channel.

**C7. Something autonomous ships with the robot.** `[KNOWN]` The press kit's "in the box" line reads "Game controller, playable before writing any code, plus autonomous behaviours at launch." What that is, a port of the prototype's brain, a subset, or the skills, is not stated; no staff comment in the launch discussion thread addresses it. Consequence: R12 and U10; the executor must be able to yield to, or switch off, an on-robot idle layer from day one, and the authority signal is the daemon's refusals, not our own gate.

**C8. The wire protocol is moving faster than any client.** `[KNOWN]` The local official checkout is API version 17 (commit of September 2); upstream main is version 23 (September 3) and adds `robot.policies`, `robot.loadPolicy`, and `robot.skills`. `[KNOWN, agent-read]` microduck-cli pins version 16 on a non-main branch. Consequence: D13 measured_on tags, 5.1 re-derived from upstream HEAD before session one, R4, and a hello handshake that refuses a mismatch.

**C9. "No license" contradicts the reuse argument.** Raised by both judges; resolved on September 5, 2026: the repository is Apache-2.0, matching upstream and every borrowed neighbor, so envelope tables, routine recipes, and the evaluation method can be reused.

---

## 2. Goals by phase, non-goals, success criteria

### Central question

How much of a Microduck's apparent character comes from which routine is chosen versus how the body performs it, and can that be measured in simulation before hardware and re-measured on the real robot?

### Phases and their goals

| Phase | Goal | Hardware | Session cap (`[GUESS]`) |
| --- | --- | --- | --- |
| P0 Contracts | This document approved; catalogue schema, event schema, API skew table, envelope protocol written | no | 1 |
| P1 Gestures and envelope, interleaved | For each of the six table-top routines: measure the channels it needs under the standing policy in CPU MuJoCo, author it inside that envelope, render a clip. Every session ends with a clip | no | 3 to 4 |
| P2 Consolidation and legibility | Complete the envelope tables (remaining channels, walking policy, both actuator models); run the blind legibility test on the six clips | no | 1 |
| P3 Loop | Thin execution layer, fake and sim adapters, random and rules backends, log and replay, mostly imported | no | 1 to 2 |
| P4 Experiment | Claude backend; three-arm blind comparison on the same scenarios and seed | no, API spend | 1 |
| P5 Hardware | Bring-up kit on the real duck, envelope re-measured, routines retuned, loop under the human gate | yes | 2 |
| P6 Later | Live-interaction feedback, preference memory, perception bridge | yes | undefined |

A phase closes on a negative finding as readily as on a positive one. A phase that exceeds its cap by more than one session is re-scoped, not extended (D11).

### Non-goals through P5

Training or modifying any policy; operator imitation; camera, microphone, or VLM perception (three neighbors already have VLM interpreters, and camera specs are provisional); mood, energy, or novelty drives beyond a reserved schema slot; reactive tracking at 5 to 20 Hz (reserved band, see section 3); multi-duck, chorale, theremin, beat sync; any edit to the external checkouts; vendoring any upstream snapshot; a dependency on `agentculture/neurosymbolic-system` (`[KNOWN, agent-read]` its Python main is a scaffold and its replacement is an unmerged Go binary).

### Success criteria

P1 and P2, envelope (complete by the end of P2):

| Criterion | Measure |
| --- | --- |
| Coverage | Every channel in 5.1 (head 4, pose 3, move 3) has a measured steady-state error, rise time, overshoot, and fall rate under both the standing and walking policy, or a recorded reason it could not be measured |
| Reproducibility | One command regenerates every table from a seed |
| Result honesty | A narrow honored range is a valid result and shrinks P2's vocabulary; it does not trigger retraining |

P1 and P2, routines and legibility:

| Criterion | Measure | Threshold |
| --- | --- | --- |
| In-envelope | Every keyframe within the P1 bounds, validator-enforced | 100% |
| Stability | Each routine plays in sim without a fall | 10 of 10 seeds |
| Legibility | Owner and one other person identify each routine from its clip, blind | Reported as a confusion matrix; no threshold; n is two and the report says so |

P3 and P4, loop and experiment:

| Criterion | Measure | Threshold |
| --- | --- | --- |
| Validity | Backend requests rejected by the validator | 0 after one tuning pass |
| Replay | Same scenario, backend, and seed reproduces the decision stream | Exact match |
| Timeliness | Decisions that miss the deadline | Reported; target under 10% at 2 s (`[GUESS]`, config) |
| Repetition | Same routine three or more times in a row without an event | Reported; random and rules arms set the floor |
| Latency and cost | p50 and p95 decision latency and cost per run per backend | Reported |
| Three-arm rating | Blind, shuffled, divergence points only, "has a character" and "what is it doing" | Reported; hypotheses, not evidence |
| Own-code size | Lines of project-authored code in the loop | Under about 600 (`[GUESS]`, a guard against scope creep) |

P5 has its own done-when in section 9. P6 is defined after P5.

---

## 3. Architecture

Three loops at three rates, which is the split both the official architecture and the most mature neighbor document. `[KNOWN]` architecture.md section 5.3: "LLM latency (hundreds of ms to seconds) means the agent is a high-level controller; reactive control stays local in robotd." `[KNOWN]` quackd ADR-0003: reflexes 50 Hz on the robot, steering 5 to 20 Hz in the agent process, deliberation about 0.2 to 1 Hz in the LLM.

```
  DELIBERATION   ~0.2 to 1 Hz, event-driven     random | rules | Claude       "what next, and why"
  (owner's computer)        │  DecisionRequest / DecisionResponse (5.7)         deadline + default
                            ▼
  EXECUTION       10 Hz tick, owns time          state machine (5.9)           validates, queues, plays,
  (owner's computer)        │  keyframe steps over daemon channels (5.3)        defaults, stops, heartbeats, logs
                            ▼
  [ STEERING      5 to 20 Hz, RESERVED           not built before P6; the band where reactive tracking
                                                  would live, ours or M9's ]
                            ▼
  BODY            FakeAdapter | SimAdapter | RobotAdapter (5.10)
                            │  move, head, look, pose, mouth, do, sound, stop
                            ▼
  REFLEXES        50 Hz on the robot             robotd: policy chain, safety, deadman   [KNOWN]
```

Beside the executor, not under it, sits the **bench**: the envelope harness (5.2) and the legibility and three-arm evaluation (5.14). The bench drives the same adapters with the same routine scripts, which is what makes a sim measurement and a hardware measurement comparable.

Decide-ahead and heartbeat are unchanged from v0.1. `[KNOWN]` The deadman defaults to 500 ms and only a twist write refreshes it; a head write explicitly does not. `[COMPUTED]` 2 Hz minimum heartbeat (1 ÷ 0.5 s); the executor ticks at 10 Hz, a 5× margin, and the robot adapter sends `robot.move` every tick, zeros included.

Authority. `[KNOWN]` The official roadmap lists finishing authority arbitration under M6, ship readiness, and the daemon reports `remoteSessionActive` and refuses calls it will not honor. The executor treats daemon refusals and that flag as the primary authority signal, and carries a copied human gate (gamepad or app active means the executor withholds every motion channel) as belt and braces.

Where things run. Deliberation and execution run on the owner's computer in every phase. The body is a fake in P3, the official CPU runner in P1, P2, and P3, and the robot daemon in P5. `[KNOWN]` The daemon's socket is `/run/robotd.sock`, JSON-RPC 2.0, forwarded over SSH on developer boards. Whether a shipped consumer unit offers a shell or a socket is UNKNOWN (U11, R13); the official WebSocket agent path is the fallback transport design when it exists.

---

## 4. Key decisions

| # | Decision | Rationale | Rejected alternative |
| --- | --- | --- | --- |
| D1 | **Vocabulary reuse: the prototype's 16 states, the daemon's 5 skills and 7 sounds.** Six table-top routines first (chill, look_around, preen, greet, stretch, sit_or_stand); locomotion and kicks after the walk envelope and, on hardware, after the floor session. | `[KNOWN]` The names are documented upstream and the primitives exist. Table-top routines need only head, look, pose, mouth, sound, and sit toggle, which are the channels P1 measures first. | Ten routines including locomotion in phase 1: adds fall risk and depends on a walk envelope not yet measured. |
| D2 | **Python 3.12, uv, one package; import `agentculture/microduck-cli` (Apache-2.0, PyPI, zero dependencies) for the JSON-RPC client, protocol table, intent bounds, write order, release-on-exit, human gate, and its fake daemon.** Attribution in appendix B. | `[KNOWN, agent-read]` Those modules exist with tests. Rewriting them is the crowded part of the landscape. `[KNOWN]` The lab and the official runner require Python 3.12. | Own client and validators: the v0.1 plan; rejected as zero-learning duplication. Rust: the daemon's language, slower to iterate for an experiment. |
| D3 | **Measure the body before authoring, on demand.** For each routine in turn: measure only the channels it needs, author it inside that measurement, render it. The envelope tables fill gesture by gesture and are consolidated in P2; every numeric bound in the catalogue cites its envelope entry. Approved September 5, 2026. | C5. Treating a learned controller as a black-box actuator with a 13-value command block, and measuring what it honors, is the robotics learning in this project, and no neighbor has done it. `[KNOWN]` Telemetry exposes `head[4]` and `joints[]` for the hardware repeat. | Author from the config caps: the caps are curriculum ceilings, not what the shipped policy learned. |
| D4 | **Three backends behind one interface: weighted random (null), deterministic rules (baseline, fallback, replay engine), Claude (contender).** Approved September 5, 2026. Memory-augmented selection is deferred to P6 with schema slots reserved now. | C3, decided. A comparison with no null arm is uninterpretable. | Two backends (v0.1). A memory backend in phase 1 (proposal 2): on synthetic streams the memory effect is authored in by the scenario writer, so it measures effort, not character. |
| D5 | **Asynchronous decisions with a deadline and a default routine.** | Unchanged from v0.1. | Synchronous loop. |
| D6 | **The execution layer is thin, mostly imported, capped at one to two sessions and roughly 600 own lines, and switched off when M9 lands.** | C1 decision; C2. | Building the brain. `[INFERRED, HIGH]` The landscape shows this is the default gravity of the hobby. |
| D7 | **Routines are data: keyframes over daemon channels only, one YAML file per routine, with ease and sound fields.** The shape follows `aj-dev-smith/microduck-mcp`'s emote files (`[KNOWN]` keys with `t`, a channel value, `ease` of smooth or hold, and a sound tag). | Scripts stay tunable by editing a file after a clip or a hardware session (R6). Nothing private reaches a motor, so the safety layer stays authoritative and the executor survives M9. | TOML as in the source project: one format for catalogue and scenarios is simpler; the shape, not the syntax, is what is borrowed. |
| D8 | **Append-only JSONL is the primary artifact**, plus envelope tables as JSON and a clip index. | Inspectability, replay, and the owner's KB constraint against hidden state. | Database. |
| D9 | **Claude backend in P4 only: `claude-opus-5`, structured output, low effort, per-request timeout equal to the deadline, a hard per-run call cap, no frames.** | `[KNOWN, from the bundled API reference]` Structured outputs via `output_config.format`; effort via `output_config.effort`. `[KNOWN, agent-read]` microduck-ai-world exhausted an account with 1,368 vision calls in about 45 minutes; the cap is that lesson. | LLM in phase 1 (v0.1): irrelevant until routines exist. |
| D10 | **The owner is the sensor before hardware.** A keyboard event console is the primary event source in P3 and P4 and the day-one path on hardware; YAML scenarios exist for replay and tests. | Removes the pretense that synthetic streams are observations; doubles as the hardware event path. | Synthetic files as the only source (v0.1). |
| D11 | **Session caps per phase, recorded in PROJECT.md; a phase closes on a negative finding.** | Hobby-tier time; R15. | Open-ended phases. |
| D12 | **The bring-up kit is a deliverable, built in P3 against the fake daemon and used in P5.** Connect with API-version refusal, record telemetry, probe head, probe pose, probe skill, probe sound, dry run, safe exit, and a printed checklist with an abort condition per step. | Day one must be a measurement session that cannot hurt the robot. `[KNOWN]` `[policy] enabled = false` runs the loop holding pose and stays healthy, which makes a no-motion connection test possible. | Ad hoc first session. |
| D13 | **Every numeric range carries `measured_on`: `config`, `sim`, `robot`, or `UNMEASURED`, plus the API version it was read against.** | C8, C5. Distinguishes a training cap from a measured range from a daemon clamp. | Bare numbers. |

---

## 5. Contracts and components

### 5.1 Primitive layer: the daemon's intents and their bounds

`[KNOWN]` Method names and parameter shapes were read from the local checkout at API version 17 and checked against upstream main at version 23; the seven sound tags are identical in both. Re-derive this table from upstream HEAD in P0 and record the commit.

| Primitive | Method | Parameters | Bound and its source (`measured_on`) |
| --- | --- | --- | --- |
| `move` | `robot.move` | `vx`, `vy` m/s, `vyaw` rad/s | `[KNOWN]` lab walk training ranges ±0.4, ±0.3, ±1.0 (config); `[KNOWN]` microduck-cli validator ceiling 0.3, 0.3, 1.5 (its source is described there as the upstream gamepad limits, not re-read); daemon clamp UNMEASURED. Refreshes the deadman. |
| `head` | `robot.head` | `neck_pitch`, `head_pitch`, `head_yaw`, `head_roll` rad, joint space | `[KNOWN]` official config caps ±1.10, ±1.10, ±1.40, ±0.31 (config, curriculum ceiling); initial ranges ±0.05, ±0.05, ±0.07, ±0.015 (config); honored range UNMEASURED until P1. Does not refresh the deadman. |
| `look` | `robot.look` | `x`, `y`, `z` m in trunk frame, `neck_pitch` | `[KNOWN]` IK solved on the daemon; floor about 0.12 m below trunk origin; reply carries the resolved joints. Preferred for gaze. |
| `pose` | `robot.pose` | `z` m, `roll`, `pitch` rad | `[KNOWN]` struct doc trained ranges z −0.025 to +0.010, roll and pitch ±0.26 (config); the daemon clamps nothing here. |
| `mouth` | `robot.mouth` | per `MouthParams` | `[KNOWN, agent-read]` 0 to 1 in microduck-cli's validator. |
| `do` | `robot.do` | `skill` ∈ ground_pick, kick_left, kick_right, sit_toggle, roulade | `[KNOWN]` doc durations about 3 s, 0.5 s, 0.5 s, unstated, 1 s; `[KNOWN]` the CPU runner keeps a kick policy active 3.0 s and a roulade 2.0 s by default, which is the window, not the motion. Reply is accepted or reason. |
| `sound` | `robot.sound` | `tag` ∈ alarm, greet, inquire, peck, chirp, coo, wheee; `hold` for wheee | `[KNOWN]` one-shot; wheee decays if holds stop arriving. |
| `stop` | `robot.stop` | none | `[KNOWN]` zeroes velocity. |
| `wait` | none | seconds | executor-side. |

New on upstream main and not yet used: `robot.policies`, `robot.loadPolicy`, `robot.skills` `[KNOWN]`. The skills query should replace the hard-coded skill list in the validator once the hello handshake reports a version that has it.

Telemetry (`robot.subscribe`): `[KNOWN]` `t`, `movement.requested`, `applied`, `limited_by` (includes `"deadman"`), `head[4]`, `policy` (walk, stand, held), `safety.fallen`, `limp`, `gravity`, `control_loop.hz`, `missed`, `joints`, `targets`, `odom`, and on main also `listening` and `part`. `[KNOWN]` Petting detection lives in the daemon (the `pet-detect` crate; the daemon "coos when petting starts") and does not appear in the telemetry struct on main, so a petting event is not available to an external client today (U12).

### 5.2 Envelope measurement harness (P1, repeated in P5)

Substrate. `[KNOWN]` The official CPU runner `microduck_rl/scripts/infer_policy.py` loads the standing, walking, sit/stand, ground-pick, kick, and roulade policies by path, has a 4-value `head_offset`, a body-pose mode, `set_vel_cmd`, the `--new-cmd-obs` flag for the 13-value command block, and `--no-bam` to switch from the BAM actuator model to the plain XML actuators. It is keyboard-driven; the harness is a small wrapper in this repository that imports its classes by path and drives the command arrays programmatically, without editing the checkout (R8: verify in session one that the classes are importable and the render path works on macOS).

Run on demand (D3): in P1 only the channels the next routine needs are swept, under the standing policy; P2 fills in the rest, including the walking policy at 0.15 m/s and both actuator models. Protocol, per policy and per channel:

1. Hold the nominal pose 2 s.
2. Step the channel to k × cap for k in 0.1, 0.2, ..., 1.0, both signs, hold 2 s each, from the config caps in 5.1.
3. Record commanded versus achieved at 50 Hz: joint angles from the simulator for head channels, trunk height and orientation for pose channels, body velocity for move channels.
4. Repeat over 5 seeds with the default domain randomization off, then with the BAM actuator model on and off.

Outputs per channel: steady-state error, rise time to 90%, overshoot, coupling (trunk tilt induced by a head command), and fall rate. Written to `envelope/<policy>.json` with `measured_on: sim`, the runner commit, and the actuator model. The honored range is the largest k with steady-state error under 15% (`[GUESS]`, a threshold to tune once the first curves exist) and zero falls. Skill timing is measured the same way: trigger, then time to the policy handing back to standing.

Hardware repeat (P5). Same protocol in 0.02 rad steps, commanded versus `head[4]` and `joints[]` from telemetry, standing only, on a table with a hand nearby, policy enabled. Written with `measured_on: robot` and the daemon's API version. The sim-versus-robot difference per channel is the project's first sim-to-real number.

### 5.3 Catalogue

One YAML file per routine, validated at load, in `catalogue/`.

```yaml
id: look_around
tier: expressive                 # idle | expressive | locomotion | skill
source: prototype:LookAround     # provenance
description: Glance left, then right, then settle.
envelope_ref: envelope/stand.json
params:
  amplitude: {min: 0.1, max: 0.5, default: 0.3, unit: rad, measured_on: UNMEASURED}
  pace: {min: 0.5, max: 2.0, default: 1.0}
duration_s: {nominal: 3.0, max: 5.0}
interruptible: true
interrupt_on: [touched, owner_feedback]
preconditions: [standing]        # standing | sitting | any
cooldown_s: 4
keys:                            # t in seconds from start, scaled by pace
  - {t: 0.0}
  - {t: 0.8, head_yaw: "+amplitude", ease: smooth}
  - {t: 1.4, ease: hold}
  - {t: 2.2, head_yaw: "-amplitude", ease: smooth}
  - {t: 2.8, ease: hold}
  - {t: 3.0, head_yaw: 0.0, ease: smooth, sound: inquire, sound_prob: 0.3}
```

Channels allowed in a key: `neck_pitch`, `head_pitch`, `head_yaw`, `head_roll` (sent as one `robot.head`), `look_x`, `look_y`, `look_z` (sent as `robot.look`), `pose_z`, `pose_roll`, `pose_pitch` (`robot.pose`), `mouth`, `sound`, `do`, `vx`, `vy`, `vyaw` (`robot.move`). The validator rejects any key outside the envelope referenced by `envelope_ref` for the active adapter and any channel the adapter does not honor.

P2 catalogue, six table-top routines. Sources are `[KNOWN]` names; compositions are proposals authored inside the measured envelope:

| id | source | composition |
| --- | --- | --- |
| `chill` | prototype:Chill | the default; slow breathing on `pose_z`, rare head micro-motion, occasional `chirp` |
| `look_around` | prototype:LookAround | head yaw sweep with holds, optional `inquire` |
| `preen` | prototype:Preen | head roll and pitch dips toward one shoulder, `mouth` opens briefly, `coo` |
| `greet` | prototype-adjacent | `look` at a bearing, `sound greet`, two small `pose_z` bobs |
| `stretch` | prototype:Stretch | `pose_pitch` forward then back, `pose_z` up, head follows |
| `sit_or_stand` | daemon:sit_toggle | `do sit_toggle`; posture belief flips on completion |

Added after the walk envelope (P3 or later) and, on hardware, after the floor session: `wander`, `turn_to`, `zoomies` (`wheee` held, hard cooldown), `ball_kick` (turn, then `do kick_*`; `[KNOWN]` blind to the ball), `ground_pick`.

Deferred with reasons: Startle, Sneeze, Ruffle, Dance (authored motion or a beat), Nap (candidate low-battery routine, R14), BallPlay (perception), Petted (`[KNOWN]` the daemon already coos locally and does not expose the event), Held (`[KNOWN]` the official ideas file says its pickup detection is deprecated and asks whether to revive or drop the state), roulade (hardware judgment; `[KNOWN]` chains while requests keep arriving).

### 5.4 Legibility test (P2)

Each routine is rendered from the sim as an mp4 and a captioned contact sheet (`[KNOWN]` the lab's `render-rollout` produces clips; the official runner's `--record` and `--save-csv` capture observations). The owner and one other person view the clips in shuffled order without labels and write what the duck is doing; a confusion matrix per routine is the output. `[COMMON]` The Godspeed questionnaire's animacy and likeability items are the standard scale for rating expressive robots and may be used as the rating form so the numbers are comparable to published work; with two raters they remain hypotheses.

### 5.5 Observations and events

```json
{"t": 12.40, "type": "person_appeared", "source": "console",
 "participant_id": "p1", "session_id": "s-2026-09-20-1",
 "bearing_deg": -35, "distance_m": 1.8, "confidence": 0.9}
```

Types: `person_appeared`, `person_left`, `person_approached`, `ball_seen`, `ball_gone`, `sound_heard` (`voice` or `noise`), `touched`, `owner_feedback` (`rating` 1 to 5, `note`), `tick`, and on hardware `fallen`, `limp`, `refused`, `battery` (`frac`). `source` ∈ `console`, `synthetic`, `sim`, `robot`, `recorded`. `participant_id` and `session_id` exist now so P6's multi-session scenarios need no schema change.

### 5.6 Context

As v0.1: `recent_events` (20), `recent_routines` (10), `repetition` (60 s window), `posture`, `cooldowns`, `preferences` (owner text plus per-routine rating averages), `time_since_last_event_s`; plus two reserved, empty slots: `drives` and `memory` (a persistent per-participant and per-routine record, unused before P6).

### 5.7 Decision request and response

Unchanged from v0.1: the request carries `request_id`, `issued_t`, `deadline_t`, the current routine and its `expected_end_t`, `catalogue_version`, and the context; the response carries `routine`, `params`, `reason`, and an optional `then` hint. A response that fails validation is logged with its verdict and replaced by the rules backend's answer; if that also fails, `chill`.

### 5.8 Execution result

Outcomes: `completed`, `interrupted`, `rejected` (by our validator), `refused` (by the daemon or the fake, first-class, never a silently dropped step), `failed`, `timed_out`. On the robot adapter `adapter_detail` carries the last telemetry `policy`, `safety`, `movement.limited_by`, and `control_loop`. One-shot skills are `completed` when their documented duration elapses with no `fallen` or `limp` seen; this is a belief and the log says so (C6).

### 5.9 Execution state machine

States `IDLE` (default routine), `PLAYING`, `STOPPING`, `FAULTED` (fallen, limp, or lost connection; manual reset only), and `YIELDED` (a gamepad or remote session is active or the daemon refused a motion call; the executor sends nothing but sound and mouth until the signal clears, then returns to `IDLE`).

Tick at 10 Hz: read adapter state and enter `FAULTED` or `YIELDED` as needed; ingest events; interrupt the current routine if `interruptible` and the event is in `interrupt_on`; emit every keyframe whose `t` has passed, interpolating by `ease`; emit the heartbeat `move` if the adapter requires it; issue a decision request when the current routine's remaining time drops under the lookahead (routine duration, capped at 3 s) with `deadline_t = min(expected_end_t, now + 2.0 s)`; validate any arrived response and queue it or replace it; at routine end pop the queue or play `chill` and log `defaulted`. A late response is logged and discarded (U6). Injectable clock for tests and replay.

### 5.10 Adapters

Interface: `start(step)`, `stop()`, `state()`, `requires_heartbeat`, `capabilities`.

**FakeAdapter (P3).** In-process, records every primitive, tracks posture, scriptable faults, latency, and refusals. Beside it, a copy of microduck-cli's `tests/fake_robotd.py` (`[KNOWN, agent-read]` a socket-level fake mirroring the daemon's replies with refuse, wedge, delay, and feed-state hooks) rehearses the robot adapter and the bring-up kit before hardware.

**SimAdapter (P1 to P4).** The official CPU runner wrapper from 5.2, which honors `move`, `head`, `pose`, and the skills; `look` is computed client-side from the runner's model (`[GUESS]` feasible; verify) or omitted in sim; `sound` and `mouth` are logged only. The lab's `WalkEnv` (`[KNOWN]` it builds the observation from `twist_cmd`, `head_cmd`, and `body_cmd` arrays) is the alternative for locomotion-only tests. The official browser simulator is a WebAssembly page (`[INFERRED, MED]` not programmatically drivable from Python without a browser harness) and is not used.

**RobotAdapter (P5).** `microduck_cli.ipc.client.RobotClient` over the forwarded socket (`[KNOWN, agent-read]` non-blocking notifications, correlated requests, bounded queue), `requires_heartbeat = true`, `robot.subscribe` at 10 Hz feeding `state()`, release-on-exit in the copied order (`[KNOWN, agent-read]` stop, pose inactive, mouth closed, sound hold off; never `robot.relax`, because a standing biped falls). Transport fallback if shipped units have no shell: the official WebSocket agent path when it exists (U11).

### 5.11 Backends

`decide(request) -> awaitable response`, cancellable at the deadline.

**RandomBackend (null).** Weighted choice among the available idle and expressive routines with a no-immediate-repeat rule; weights modeled on the official Reachy Mini conversation app's idle policy (`[KNOWN, agent-read]` 0.60, 0.16, 0.16, 0.08 renormalized over available moves). Seeded.

**RulesBackend (baseline, fallback, replay).** Priority list as v0.1: interrupt-worthy event first (`greet` toward a person, `preen` after `touched`; later `turn_to` then `ball_kick`), low owner rating avoids a routine for 120 s, no event for 20 s rotates among `look_around`, `stretch`, later `wander`, never the same twice; `zoomies` at most once per 60 s. Floor: three safety inhibits copied from microduck-cli's default rules (`[KNOWN, agent-read]` fallen inhibits, low battery under 0.15 inhibits, stop when limp). Deterministic given `(request, seed)`.

**ClaudeBackend (P4).** As D9. Stable system block (catalogue, pet rules, output schema) followed by per-request context, so prompt caching applies (`[KNOWN, from the bundled API reference]` prefix-based, minimum cacheable prefix is model-dependent, verified through `usage.cache_read_input_tokens`). Wall-clock latency and `usage` logged per call; a hard per-run call cap in config; events only, no frames.

One TOML config selects backend, model, deadline, lookahead, catalogue, adapter, scenario or console, seed, log path, call cap.

### 5.12 Logging, replay, clips

One JSONL per run: `run_start` (config, catalogue version, envelope versions, git SHA, API version), `event`, `decision_request`, `decision_response` (latency, backend, usage), `validation`, `routine_start`, `primitive`, `routine_end`, `defaulted`, `refused`, `fault`, `yield`, `run_end`. `replay <log>` re-runs with the rules or random backend and diffs the decision stream; a Claude run replays from logged responses. `report <log>` computes section 2 metrics. Envelope tables and the clip index are separate JSON files referenced by the run.

### 5.13 Scenarios and sessions

S1 quiet room, S2 someone arrives, S3 ball, S4 feedback are kept from v0.1 as executor and replay tests. Console sessions are the primary source in P3 and P4. S5 (returning participant across three sessions) and S6 (two participants with opposing feedback) are written in P0 so the schema is proven, and run only in P6. S-real-n are recorded hardware sessions that replace synthetic streams as the evaluation set once they exist.

### 5.14 Evaluation

Legibility confusion matrix (5.4). Three-arm comparison: same scenario or recorded session, same seed, each backend; rendered sim clips where the sim adapter is in use; ratings entered blind on shuffled, unlabeled decision streams at divergence points only; report shows the section 2 metrics, a disagreement count, and the ratings with arm labels revealed afterward. Standing note in every report header: with one or two raters, results are hypotheses.

### 5.15 Repository layout and tooling

```
microduck/
  DESIGN.md  PROJECT.md  README.md  AGENTS.md
  agent/                          # Python 3.12, uv
    pyproject.toml
    src/petagent/
      catalogue.py  events.py  context.py  executor.py  clock.py  log.py  config.py
      envelope/   sweep.py  report.py          # 5.2
      adapters/   base.py  fake.py  sim_runner.py  (robot.py P5)
      backends/   base.py  random.py  rules.py  (claude.py P4)
      bringup/    cli.py                        # 5.16, P3 build, P5 use
      console.py  cli.py                        # run | replay | report | console
    catalogue/*.yaml   envelope/*.json   scenarios/*.yaml   clips/index.json
    tests/
```

Dependencies through P3: `pyyaml`, `pydantic`, `pytest`, `microduck-cli`, plus the official runner's `mujoco` and `onnxruntime` for the sim adapter (installed in this package's own environment; the checkouts are not edited). `anthropic` in P4. Tests: catalogue validation and envelope enforcement, state machine transitions with a fake clock (deadline miss, interrupt, fault, yield, refusal, cooldown), backend determinism, replay exact-match, bring-up kit commands end to end against the fake daemon, Claude backend behind recorded fixtures.

### 5.16 Bring-up kit (P3 build, P5 use)

Commands: `connect` (hello, print and refuse on API-version mismatch), `record` (telemetry JSONL at 10 Hz), `probe-head`, `probe-pose` (0.02 rad or 2 mm steps, log commanded versus telemetry), `probe-skill` (trigger and time until `policy` returns to standing), `probe-sound`, `dry-run` (print exactly what would be sent), `safe-exit`. Day-one order, each step with an abort condition: policy disabled connection test; `robot.enable`; `chill` only on the table; head probes; pose probes; the six routines; floor work in a later session. Sessions are sized under 45 minutes (`[KNOWN]` press kit: 2,600 mAh battery, "around one hour of runtime depending on use").

---

## 6. Risks and unknowns

| # | Risk | Basis and band | Mitigation |
| --- | --- | --- | --- |
| R1 | Claude misses a 2 s deadline often enough to feel dead | `[GUESS]`, unmeasured | Logged from run one; deadline is config; rules fallback; P4 only |
| R2 | Honored head and pose range is narrow | `[KNOWN]` initial training ranges are tiny; final unknown; `[INFERRED, MED]` | P1 measures; a narrow result shrinks P2 and is a finding |
| R3 | Skill completion unobservable on hardware | `[KNOWN]` | Time-based belief, labeled; `probe-skill` measures the window |
| R4 | API drift before delivery | `[KNOWN]` 17 local, 23 main, 16 in the imported client | Hello refusal; re-derive 5.1 from HEAD in P0; `measured_on` carries the version |
| R5 | M9 and authority conflict | `[KNOWN]` M6 item, open question upstream | Daemon refusals and `remoteSessionActive` are the signal; `YIELDED` state; D6 |
| R6 | Blind-authored scripts look wrong on the real duck | `[INFERRED, HIGH]` | Scripts are data; P5 retunes after probes |
| R7 | `wander` without obstacle input walks into furniture | `[KNOWN]` avoidance is on-robot and unported | Sim only until an obstacle input exists |
| R8 | The CPU runner's classes are not importable or the render path fails on macOS | `[GUESS]`; `[KNOWN, agent-read]` microduck-ai-world needed an offscreen GL context and fell back to blind | Session-one check; the lab's `WalkEnv` and `render-rollout` as the fallback substrate |
| R9 | Sim envelope overstates the servos | `[KNOWN]` the runner has a BAM actuator model and a plain-XML option; `[KNOWN, agent-read]` the lab README says its env is not the sim-to-real recipe | Measure under both actuator models; treat the narrower as the bound; P5 repeats on hardware |
| R10 | Two raters | `[COMMON]` | Hypotheses, stated in every report |
| R11 | Neighbor projects are single-author with days of history and may vanish | `[KNOWN, agent-read]` | Copy with attribution; pin the PyPI version; never depend on an unmerged rewrite |
| R12 | Autonomous behaviors ship at launch and contend for the body | `[KNOWN]` press kit line; content unknown | `YIELDED`; day-one check of what runs at boot; U10 |
| R13 | Shipped units may offer no shell or socket | UNKNOWN | U11; WebSocket agent path as fallback design |
| R14 | Battery bounds every hardware session | `[KNOWN]` about one hour | Sessions under 45 min; `battery` event; Nap as the low-battery routine later |
| R15 | The bench eats the project and the duck never moves | `[INFERRED, HIGH]` | D11 caps; every session ends with a clip, a table, or a log |
| R16 | No license blocks reuse of the measurements | Closed: Apache-2.0 added September 5, 2026 | U9 |

---

## 7. Deliberately not designed here

Perception bridge and virtual camera (three neighbors have VLM interpreters; camera specs are provisional); preference learning and persistent memory beyond the reserved slots; drives and mood; reactive steering; social and beat-synced behaviors; a Rust rewrite; anything requiring changes to the external checkouts.

---

## 8. Phase map

| Phase | Body | Events | Adds |
| --- | --- | --- | --- |
| P0 | none | none | this doc approved; schemas; API skew table; envelope protocol |
| P1 | official CPU runner | none | six routines with clips, each with the envelope entries it needed |
| P2 | official CPU runner | none | complete envelope tables (standing, walking, both actuator models), legibility matrix |
| P3 | fake, then runner | console and S1 to S4 | executor, random and rules, log, replay, bring-up kit against the fake daemon |
| P4 | runner | console and S1 to S4 | Claude backend, three-arm blind comparison, cost and latency |
| P5 | robot | console, then recorded | connection test, probes, envelope on hardware, routines retuned, loop under the human gate |
| P6 | robot | recorded, real participants | feedback loop, memory, perception |

---

## 9. Milestones and done-when

| Milestone | Deliverable | Done when |
| --- | --- | --- |
| P0 | `DESIGN.md` v0.2 approved; `catalogue/` schema; `scenarios/` S1 to S6; `docs/api-skew.md` | Schemas load under a test; the skew table names every method and shape against upstream HEAD with its version; the owner has struck or added routines |
| P1 | six routine files, `clips/`, partial `envelope/stand.json` | Each routine 100% within its measured channels; 10 of 10 seeds without a fall; a clip per routine; every session closed with a clip |
| P2 | complete `envelope/stand.json` and `envelope/walk.json`, a table in `PROJECT.md`, legibility matrix | One command regenerates both tables; every channel has numbers or a reason, the walk-policy head result recorded even if narrow; two raters' confusion matrix recorded |
| P3 | executor, fake and sim adapters, random and rules backends, console, log, replay, bring-up kit | S1 to S4 replay exactly under both backends; every kit command runs against the fake daemon; tests pass with no network; own-code line count reported |
| P4 | Claude backend, report | all four scenarios under three arms; blind ratings recorded before labels; latency, cost, deadline-miss rate reported; a one-paragraph verdict in `PROJECT.md`, including "indistinguishable" if that is the result |
| P5 | hardware envelope, retuned catalogue, recorded sessions | connection test passes with policy disabled; `chill` and three head or pose routines play without a fall; envelope table has a robot column; first sim-to-real difference recorded |
| P6 | defined after P5 | |

---

## 10. Traceability: high level to detail

| High-level item | Satisfied by |
| --- | --- |
| Central question (section 2) | 5.2 envelope, 5.4 legibility, 5.14 three-arm comparison, P5 hardware repeat |
| C1, D6 thin disposable loop | 5.9 state machine, 5.15 own-code line count, P3 cap, appendix B imports |
| C2, D2 reuse | 5.10 adapters import the client and fake daemon, 5.11 safety floor rules, 5.1 bounds cite the validator, appendix B |
| C3, D4 three backends | 5.11 random and rules and Claude, 5.14 disagreement and blind rating, P4 done-when accepts "indistinguishable" |
| C4 live evaluation last | section 2 has no live-interaction criterion before P6; 5.13 S5 and S6 reserved; 5.6 memory slot |
| C5, D3 measure first | 5.2 harness, 5.3 `envelope_ref` and validator, 5.1 `measured_on`, R2, R8, R9, P1 interleaves measurement and authoring, P2 consolidates |
| C6 | 5.8 belief outcomes, 5.16 `probe-skill`, R3 |
| C7, R12 | 5.9 `YIELDED`, section 3 authority, U10 |
| C8, D13, R4 | 5.1 versions, P0 skew table, 5.16 `connect` refusal |
| C9, R16 | U9 |
| D1 vocabulary and six routines first | 5.3 table and deferred list |
| D5 asynchrony | 5.9 lookahead and deadline, 5.12 `defaulted`, U6 |
| D7 scripts as data | 5.3 keyframe format, R6 |
| D8 JSONL | 5.12, 5.14 reads it |
| D9 Claude in P4 | 5.11, P4 milestone |
| D10 owner as sensor | 5.5 `source: console`, 5.13, 5.15 `console.py` |
| D11 caps | section 2 table, R15 |
| D12 bring-up kit | 5.16, P3 and P5 milestones, R13, R14 |

Consistency check while writing: every channel in a 5.3 key maps to a 5.1 method; every outcome in 5.8 has a producing transition in 5.9; every section 2 metric has a 5.12 record; every risk is referenced from a section above; every phase in section 8 has a milestone in section 9.

---

## 11. Decisions for the owner

| # | Question | Recommendation |
| --- | --- | --- |
| U1 | Adopt the re-scope: body and experiment as the centerpiece, loop as an imported enabler? | **Approved September 5, 2026.** |
| U2 | Six table-top routines first, locomotion after the walk envelope and the floor session? | **Approved September 5, 2026.** |
| U3 | Claude backend deferred to P4, with a hard call cap and no frames; model `claude-opus-5` at low effort by default? | **Approved September 5, 2026.** The catalogue is data and grows by adding files; rigidity is addressed by expanding it and by per-routine parameters, not by moving the LLM earlier. |
| U4 | Drives and memory deferred to P6 with schema slots reserved now? | Yes. |
| U5 | Sim substrate: the official CPU runner wrapper, with the lab environment as fallback? | Yes; decided finally in session one (R8). |
| U6 | Late decisions discarded? | Yes until latency data exists. |
| U7 | `wander` sim-only until an obstacle input exists? | Yes. |
| U8 | Import `microduck-cli` modules with attribution (Apache-2.0) rather than rewriting them? | **Approved September 5, 2026:** borrow where necessary, with attribution (appendix B). |
| U9 | License | **Decided September 5, 2026: Apache-2.0.** `LICENSE` added. |
| U10 | What ships as "autonomous behaviours at launch"? | Owner agreed to ask upstream; issue text drafted September 5, 2026, owner to post. Design for `YIELDED` regardless. |
| U11 | How does a customer get a shell or socket on a shipped unit? | Asked together with U10; keep the WebSocket agent path as the fallback. |
| U12 | Request a petting event in telemetry upstream? | Yes, a small issue citing the `pet-detect` crate; it is the most valuable owner-interaction event and the daemon already detects it. |
| U13 | Session caps as in section 2? | Yes, and record them in `PROJECT.md`. |
| U14 | Measure on demand rather than sweep first? | **Approved September 5, 2026**; D3, section 2, 5.2, 8, 9 updated. |
| U15 | When does the LLM arm enter? | Delegated to the design: P4 as written. Reason: the experiment needs the six routines and the random and rules arms to exist first, and pulling Claude into P3 would breach P3's cap; if P3 closes under its cap, the Claude backend may start in the same session. |

---

## Appendix A. Verified landscape (September 5, 2026)

Two projects were reviewed at source level and 18 more were surfaced by a five-angle search and each checked by an independent verifier that opened the URL and read code or paper; none was refuted. `[KNOWN, agent-read]` unless marked. Relevance is the verifier's 1 to 5 score against this project's question.

| Project | License | What it is | Rel. | Use here |
| --- | --- | --- | --- | --- |
| shaibuafeez/microduck-ai-world | Apache-2.0 | One squashed commit vendoring two upstream snapshots; a Python sim brain (one VLM call per 5 s roaming, 1.8 s seeking; action whitelist; Lissajous wander fallback) and a Rust robot daemon whose `move`, `do`, and `sound` payloads are rejected by its own vendored daemon; no catalogue, memory, evaluation, or tests for original code; maturity 2 | reviewed | Stale-intent handoff pattern; output hardening trio; the cost lesson (D9) |
| agentculture/microduck-cli | Apache-2.0 | 50 Hz rules and arbitration engine, JSON-RPC client, transcribed protocol table, validators with cited bounds, release-on-exit, human gate, fake daemon, JSONL record and replay; sim and fake only; pinned to API 16 on a non-main branch; its declared dependency does not exist yet; maturity 2 | reviewed | Imported and copied modules (appendix B) |
| Daphilippe/microduck_remote_brain | none | Off-board VLM brain (local Ollama) producing a schema-validated scene state; per-cycle capability refresh from telemetry; sim only | 4 | Design reference only: capability refresh and a "physical profile" with movement disabled for a first hardware session |
| rokbenko/quackd | Apache-2.0 | LLM task pilot picking one existing verb per turn under a contract with allowlist, budgets, confirm gates, heartbeat; bundled sim; on PyPI; ADR-0003 documents the three loops `[KNOWN]` | 4 | Section 3 reference; second transcription of method names for cross-checking |
| aj-dev-smith/microduck-mcp | Apache-2.0 | MCP server and CLI over a CPU MuJoCo sim running the official policies; TOML behavior machines and keyframe emotes `[KNOWN]` | 4 | Script format shape (D7); its head-roll cap of 0.30 is one author's comment, not a measurement |
| pollen-robotics/reachy_mini_conversation_app | Apache-2.0 | Official sibling-robot app: a realtime voice LLM issues tool calls over a move library, with a weighted-random idle policy and a small memory file | 4 | Random backend weights; memory file shape for P6 |
| aethexai/reachy-mini-snoopy | MIT | Rule-based "living pet" personality on a 0.4 s tick with a no-repeat picker | 4 | No-repeat picker and event pre-emption pattern |
| rockywuest/pidog-embodiment | MIT | Brain and body split for a quadruped toy; forced JSON output over a fixed action list; dwell and confirm guards | 4 | Transition guards when drives are revisited |
| kercre123/victor | none (leaked source) | Anki Vector engine including its mood system with decay graphs | 4 | Design reference only, never code; legal status not established |
| marceld23/Ai-Robo-Dog | MIT | LLM agent over 45 enum-constrained tools for a toy quadruped | 4 | Evidence for C2 |
| xujiayuxian-png/microduck-habitat | Apache-2.0 | Desktop virtual pet with a small drives model choosing among seven activities | 3 | Drives baseline shape for P6 |
| craigm26/OpenCastor | Apache-2.0 | Robot-agent framework with a real Microduck driver (JSON-RPC with deadman) and a choreography module of primitives and routines with `duration_s` and `exclusive` `[KNOWN]` | 3 | Routine step-list shape; driver-side deadman precedent |
| pollen-robotics/reachy_mini (SDK) | Apache-2.0 | Official SDK with agent guides on motion philosophy, control loops, and interaction patterns | 3 | Reading for P2 authoring |
| haasonsaas/jarvis | none | Voice assistant with a 30 Hz presence state machine for the sibling robot | 3 | none |
| seven-lynx/HoundMind | GPL-3.0 | Hardware-only quadruped runtime with a reactive FSM behavior tier | 3 | Read only |
| Br3nd4n67/VectorMind | MIT | Local-LLM stack for Vector with per-face memory | 3 | Memory reference for P6 |
| kercre123/wire-pod | MIT | Community Vector server whose LLM replies embed command tokens mapped to animations | 3 | Evidence for C2 |
| jbeghtol/openmoxie | MIT | Replacement server for a companion robot with rule-based gesture markup of LLM text | 3 | none |
| 3D-aslan/cozmo-direct-control | none | LLM replies with inline mood and action tags | 3 | none |
| kai-zhang-er/duck-harness | none | Adapter protocol and MuJoCo adapter, no README | 2 | none |

Dropped by the verification cap (34 candidates, lowest searcher confidence), listed so the omission is visible: research papers on LLM-generated expressive robot behavior (GenEM; the Haru tabletop-robot paper; ProAct; behavior-tree generation for social robots; a survey of LLMs in socially assistive HRI; an episodic-memory evaluation on a humanoid head; a Reachy Mini low-DoF emotional-expression study), Petoi and Cozmo behavior projects, an official Reachy Mini emotions and dances library, `py_trees`, `arbitration_graphs`, and `transitions`. The research papers are the first thing to read before P2 authoring and P4 experiment design; none was verified in this pass.

Prototype lineage, checked directly `[KNOWN]`: `apirrone/microduck_runtime` is not publicly reachable; `apirrone/microduck_sounds` and `apirrone/microduck_pet_detect` are public without a license; `apirrone/Open_Duck_Mini` is Apache-2.0 and `apirrone/Open_Duck_Mini_Runtime` is public without a license. The community index `joeynyc/awesome-microduck` marks every hardware-facing tool as pre-validation.

## Appendix B. Borrowed code and licenses

To be kept current in `PROJECT.md` as well.

| Module | From | License | How |
| --- | --- | --- | --- |
| JSON-RPC client, protocol table, intent bounds and validators, write order and edge-trigger rule, release-on-exit, human gate, liveness guard, injected clock pattern | agentculture/microduck-cli | Apache-2.0 | import from PyPI where clean, copy with header attribution otherwise |
| Fake daemon for tests | agentculture/microduck-cli `tests/fake_robotd.py` | Apache-2.0 | copy |
| Keyframe emote shape | aj-dev-smith/microduck-mcp | Apache-2.0 | shape only, own YAML |
| Three-loops framing | rokbenko/quackd ADR-0003 | Apache-2.0 | cited |
| Stale-intent handoff, output hardening | shaibuafeez/microduck-ai-world | Apache-2.0 | pattern, own code |
| Idle policy weights | pollen-robotics/reachy_mini_conversation_app | Apache-2.0 | values, own code |
| CPU runner classes | pollen-robotics/microduck_rl `scripts/infer_policy.py` | Apache-2.0 | imported by path from the local checkout, unmodified |
| Design references, no code | Daphilippe/microduck_remote_brain, kercre123/victor | none | read only |
