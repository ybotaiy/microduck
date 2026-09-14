# Microduck capability roadmap

Updated September 13, 2026. **Planning revision only; no new simulation, training or hardware work performed.** The proposed replacement-controller long run is withdrawn as the next recommendation. Existing results remain evidence, including failures.

## Direction

Build an understandable, responsive robot companion by adding useful behaviors to the working gait and rules controller. Preserve a simple solution that already works. Add training, a planner or another abstraction only when a measured limitation warrants it; a different implementation is not automatically a new capability.

The next recommended visible improvement is **obstacle-aware ball pursuit on a flat simulated floor**: stop before a blocking object, then take a simple verified clear route around it and continue following. This is a proposal for approval, not an implemented capability. A blocked route must end in a bounded stop rather than repeated attempts.

## What exists today

| Capability | Evidence and limits |
| --- | --- |
| Standing, controlled push recovery, coordinate-based approach and moving follow | Demonstrated with XML position actuators; not BAM dynamics or hardware. [Simulation report](docs/2026-09-09-simulation.md), [moving follow](DYNAMIC_FOLLOW.md). |
| Image-based ball approach, stop/resume and bounded rear/side search | Rules use an idealized camera and a colored-ball detector above the existing gait. Demonstrated scenarios are not unrestricted reliability. [Bounded search](BOUNDED_SEARCH.md). |
| Recovery after temporary occlusion | The obstruction is removed before pursuit resumes. This is not navigation around an obstacle. |
| Learned replacement visual controller | Partial experiment: static success, moving failures, and no demonstrated new capability. Keep it as an optional research artifact, not the operational baseline. [Results](VISUAL_CONTROLLER.md), [evidence audit](RUN_REVIEW_2026-09-13.md). |
| Obstacle avoidance, edge protection and real-world interaction | Not implemented or validated. Sensor research is a starting point, not proof of working sensing or safety. [Hardware signals](HARDWARE_SIGNALS.md). |

## Build order and observable outcomes

| Stage | What the duck gains | Smallest useful approach | Evidence required to move on |
| --- | --- | --- | --- |
| 0. Preserve the foundation | Keeps its existing chase, stop/resume and search behavior | Retain gait and rules. Fix only evaluator defects needed for trustworthy new experiments; preserve the unfinished learner work separately. | Reproduce relevant baseline cases; schedule-aware scoring and acceptance commands that fail on behavioral failures. No broad retraining prerequisite. |
| 1. Notice a blocked path and stop | Stops before a stationary obstacle even when the ball is beyond it | Add a bounded simulated range-sensing interface informed by the advertised coarse ToF sensor, with explicit geometry, validity and timing assumptions. Add a final motion veto. Measure actual stopping travel and turning sweep. | Obstacles in the commanded swept path trigger a stop with measured clearance; missing/stale/invalid range data veto motion. Include clear-path controls to expose an always-stop solution. Ground truth is used for evaluation, not controller obstacle coordinates. |
| 2. Go around a simple obstacle | Reaches the ball around a box; stops when there is no supported route | Extend the existing state machine with bounded look/choose-clear-side/turn/advance/reacquire behavior. Start with one static obstacle on flat ground. Retain obstacle veto through every maneuver. | New left/right layouts and initial poses, no detected obstacle/ball contact or falls, successful target approach/stop, blocked-path timeout and relevant chase regressions. Record both successes and limits. Stop if sensing cannot verify the next swept region; do not assume side clearance from a front reading. |
| 3. Make interaction coherent | Looks toward the target, follows, waits, searches briefly, and disengages predictably | Compose supported actions using a small rules-based state machine, completion feedback and manual stop. Add a few expressive head/pause routines only within measured limits. | Short readable interaction sequences, reliable interruption, no conflicting actions or endless retries. Human feedback assesses whether behavior is understandable; attention alone is not enjoyment. This can follow stage 1 in a stationary/bounded form if navigation work stalls. |
| 4. Transfer to the actual robot | Performs a limited verified subset outside simulation | When hardware is available, check actual sensor coverage/calibration, latency, odometry and stopping behavior before supported floor-level trials. Reuse existing components where they pass. | Supervised commissioning and explicit manual stop; measured operating envelope. Simulation success does not certify hardware, edge safety or interaction around participants. Unsupported behaviors stay disabled. |
| 5. Extend only where evidence warrants | Gains a specific missing ability or measurable robustness improvement | Use the cheapest effective method: rules, better observations, controller adjustment, then learning if justified. Investigate dynamic obstacles, richer perception or edge sensing separately. | Before investing, name the failing use case, compare the simple baseline, define the useful gain and cost, and retain a fallback. Educational training is a separate explicit objective. |

Stages 1 and 2 are the recommended next feature sequence. Stage 1 alone is useful obstacle stopping, but must not be reported as successful avoidance. Stage 2 may require a smaller supported layout envelope if sensor coverage is inadequate; a full map, SLAM, general planner, new gait or learned chase controller is not an automatic prerequisite.

## Meaning of generalization

For a new obstacle behavior, test different unseen obstacle positions, widths, target locations and approach angles within a stated supported envelope. That checks whether the added behavior works beyond its demonstration. It does not require machine learning. Keep development cases distinct from final tests; do not spend hours replacing already-working clear-floor chase merely to call the replacement generalized.

## Next approved-run proposal to prepare

Use one bounded implementation plan covering stages 0–2 and their failure branches. Freeze measurable clearance, timing, target-stop and contact/fall criteria after a short sensing/stopping feasibility check and before final testing. A feasibility adjustment must be documented; do not relax a failed final gate. Reserve novel layouts for final acceptance and retain known failures as development cases.

Success should be understandable from three reviewed simulation clips: (1) obstacle ahead causes a stop; (2) a clear side permits a detour followed by ball approach/stop; (3) a fully blocked or uncertain route ends stopped. Pair clips with exact recorded-run metrics and a baseline comparison. A simple clear-floor follow regression completes the evidence. No new GIFs are claimed by this planning revision.

### Budget from measured work, not a desired number of hours

The [runtime audit](RUN_REVIEW_2026-09-13.md) measured median moving episodes of about 23 seconds with camera sensing and 46 seconds with recording. The earlier artifact windows were about 22 and 54 minutes, not multi-hour training; neither is a full session-duration measurement. New range sensing and detour episode lengths must be benchmarked before extrapolation.

For example, 60 comparable camera-only episodes plus 12 recorded episodes would consume about 32 minutes of rollout time at those medians. Implementation, diagnosis and review are additional and uncertain. A few-hour window is justified by building and validating the new capability, not inflating episode counts or training an unnecessary model.

A future run can use a four-hour working budget plus a reserved hour for final evidence, review and delivery, with explicit branches: baseline/evaluator repair; sensor/stop feasibility; simple detour; frozen evaluation. Re-estimate after the initial benchmark and record phase timings. If stopping works but detour remains unsupported, deliver a clearly partial feature with failure evidence at the deadline. If all scoped work and delivery finish early, finish early. Approval of this roadmap alone does not launch that run.

## Autonomous execution and delivery contract

Once a concrete run is approved, perform routine diagnosis, bounded fixes, evaluation, results review, roadmap updates, privacy audit and verified GitHub publication without further routine user intervention. Record a resumable stage ledger, source/config hashes, start/deadline, commands, outcomes and next recovery action. A failed experiment advances to the next approved useful branch; do not stop merely because one candidate failed. Finish on achieved acceptance, exhausted authorized recovery or the deadline, followed by closeout. Do not promise success regardless of evidence or continuity after app/machine shutdown.

All work stays local: no paid APIs, purchased credits, cloud compute or new service charges. Do not use hosted inference, even a free tier with possible billing. Ordinary Git publication must avoid billable workflows, LFS or deployment side effects. Existing application billing and machine operating costs are outside this plan's control. No hardware experiments or purchases are authorized by a simulation plan.

Closeout includes a dated PASS/PARTIAL/BLOCKED report, measured counts and timings, inspected GIF evidence, failures, updated current project state and ranked next steps. Review the full outgoing commit range, exact staged file allowlist, author metadata, logs and media for secrets, private context, machine paths and personal content. Fix issues before upload; never copy private KB material into this public repository. Preserve unrelated work and published history. Verify the delivered remote commit and artifact paths; an attempted push is not delivery. Record external blockers honestly after authorized recovery is exhausted.

## Historical records

- [Archived visual-controller plans](OVERNIGHT_PLAN_ARCHIVE.md): previous scope and acceptance contract, no longer the next work queue.
- [September 13 evidence and runtime audit](RUN_REVIEW_2026-09-13.md): findings remain relevant; its replacement-training proposal is superseded.
- [Character Bench design](DESIGN.md): historical architectural ideas, not mandatory prerequisites. Cloud-selector and elaborate comparison work are deferred under the current local-only scope.
