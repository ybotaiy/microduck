# Evidence audit and proposed long run

September 13, 2026. **Proposal only; no new training or rollouts started during this audit.**
This review supersedes earlier duration estimates and completion wording for the next run.

## Findings

| Model | Latest ten moving cases, camera sensing only | Same cases with presentation video |
| --- | --- | --- |
| Published visual controller v1 | 10/10 | 9/10 |
| Local candidate v2 | 9/10 | 10/10 |

Counts come from saved summaries. Neither model meets the cross-mode gate. The v1 recorded failure ends at 0.592 m; the v2 camera-only failure ends at 0.422 m, beyond the 0.40 m maximum. The local v2 candidate has not repeated the static/blackout/search regression battery. Published v1 passed the 12-position static grid, blackout recovery and rear search; search remains a rules-based wrapper above the unchanged gait.

The audit corrects several earlier interpretations:

1. **Wrong pause/departure scoring:** custom trajectories changed event times, but `analyze_follow` retained the original pause windows (0–8, 16–23, 31–42 seconds). Read-only re-scoring using each saved actual schedule changes the first suite from rules 3/10 to 6/10 and learned 3/10 to 8/10, retaining the other existing checks. These are diagnostic reanalysis counts, not a newly validated acceptance implementation. The earlier claim that 3/10 established an overly difficult suite was unsupported.
2. **The added boundary examples did not enter training:** the generator appended 1,224 examples after 52,720 existing ones, then split at index 43,155. Every added example landed in validation. Training gained 979 existing examples (derived: 43,155 minus 42,176). The improvement cannot be attributed to training on the appended boundary examples.
3. **The moving suites are development evidence now:** paths were changed after failures, the same suite ID was retained, and model correction used observed test failures. Case 0 also repeats the old scripted follow. Keep these results; do not label them fresh held-out evidence.
4. **Render causality remains unresolved:** the successful diagnostic rerun started the ball at (0.8, 0.35), while the old failing case used (0.6, 0.05). That comparison cannot refute the old failure. The matching-origin v1 comparison still reproduces it. Shared renderer state, pixel differences and controller sensitivity need controlled tests.
5. **Batch exit codes ignore behavioral failures:** both batch evaluators only exit nonzero for failed subprocesses. A completed process can report failed behavior and still exit 0. Unattended completion needs authoritative acceptance checks.
6. **Teacher state/cadence mismatch is a hypothesis:** teacher resume decisions use dwell time; the learner sees bearing, size and its last command, with no explicit dwell input. Synthetic observations advance at 0.1 s, deployed control at 0.02 s, and RGB at 0.04 s. Test whether elapsed-time/history features are necessary after fixing the splits; this is not yet a proven root cause.

## Measured runtimes

Sources: existing ignored `summary.json` timers and artifact modification times. No new simulation was needed.

| Work | Measured result |
| --- | --- |
| First run: 42 completed rollouts | 14.10 min summed rollout timers; approximately 22.07 min artifact window |
| Follow-up: 86 completed rollouts | 44.93 min summed rollout timers; approximately 53.51 min artifact window |
| Moving rollout, camera sensing only | Median 22.72 s across 55 runs; range 20.42–47.84 s |
| Moving rollout, presentation recorded | Median 45.69 s across 35 runs; range 44.60–80.85 s |
| Latest ten-case candidate suite, camera-only | 3.87 min summed timers; 3.90 min artifact window |
| Latest ten-case candidate suite, recorded | 8.03 min summed timers; 8.06 min artifact window |
| Training alone | Optimizer wall time was not logged; do not invent a training-duration total |

Aggregate minutes are derived from summed timer seconds divided by 60. Artifact windows are estimated as last summary modification time minus the earliest modification time less its logged rollout duration, divided by 60. They exclude work outside the saved artifacts and are not full task durations or model-reasoning measurements. Interrupted runs without summaries are absent. Medians/ranges are derived from the stated samples.

RGB rendering accounts for about 83% of camera-only follow time (derived: summed RGB stage times divided by summed follow wall timers). Physics and gait inference together account for less than 2%. Longer optimizer runs alone are not a justified way to fill several hours.

Budget **30 s per typical 42-second camera-only rollout** and **60 s per recorded rollout**, rounded above recent medians. Rebenchmark longer search episodes at launch. Ten trajectories for two controllers in both modes need roughly 23 min (derived estimate: (20×30 + 20×60)/60). Training needs a separately timed pilot.

## Proposed run: 4½-hour target, five-hour cap

All phase durations are planning allocations, not measured coding estimates. The extra half hour is recovery capacity. Preserve local-only compute, no paid APIs/services/credits, unchanged gait, simulation-only work, privacy review and verified GitHub delivery. One approval covers the full proposed sequence through publication without routine intervention.

| Elapsed target | Work and bounded quantity | Evidence and failure branch |
| --- | --- | --- |
| 0:00–0:35 | Fix schedule-aware scoring, nonzero acceptance failures, invalid/truncated trace rejection, versioned manifests and episode splits. Rescore saved traces. Add resumable per-case status, timeouts and an elapsed-time ledger. Benchmark moving and longer search cases. | Tests must reject do-nothing behavior, missed departures and failed outcomes. Preserve thresholds and failed cases. |
| 0:35–1:00 | Up to eight matched camera-only/recorded pairs with identical origins, schedules, source/model hashes and seeds. Find the first differing observation, command and physical state; test isolated presentation renderer/state. | Prove a cause or retain the uncertainty. Adopt a render change only after validating control preservation. |
| 1:00–2:00 | Fix episode-disjoint training/validation; assert boundary rows reach training. Collect up to 40 learner-visited development episodes with teacher labels. Train three seeds, at most one further revision per seed, and up to ten validation episodes per candidate. Time every fit. | Choose by validation, not final tests. Add time/history features only if needed. No teacher fallback during learned inference. Freeze one candidate at hour two. |
| 2:00–3:50 | New final manifest: 50 behavior episodes per controller for learned, rules, untrained and always-stop; ten moving cases additionally recorded for learned and rules; ten learner fault episodes. Include legacy regressions. | About 230 episodes (derived: 50×4 + 10×2 + 10). Use identical manifests across controllers, retain every failure and keep final data out of selection. |
| 3:50–4:30 | Review results and four GIFs; update findings/roadmap; preserve reproducibility and training metadata; audit outgoing text/model/media/commit metadata; publish using existing authentication and verify remote SHA and artifacts. | Exact pass/fail coverage, measured timings, privacy-reviewed GitHub delivery. Promotion requires acceptance. |

The final matrix is about 100 min of raw simulation at observed moving medians (derived estimate: (200×22.72 + 20×45.69 + 10×30)/60), or 125 min using conservative 30/60-second rates. The 110-minute final stage plus up to 30 minutes recovery covers that range. Longer searches and extra regressions must be re-estimated at launch; reduce speculative trials or optional stress work if needed, not required acceptance coverage. Preserve 40 minutes for delivery. No throughput guarantee is implied.

## Acceptance and stopping

- Treat all existing moving cases as development/regressions. Freeze new train/validation/final/reserve episode seeds and trajectory hashes before fitting; audit duplicates. Never redraw final cases because a controller fails. Report baseline failures and use separate development cases for diagnosis.
- Final behavior has ten episodes each for static approach, moving follow/pause/resume, rear search, repeated side reacquisition, and recoverable loss/occlusion. Require at least 45/50 overall and at least 8/10 in every family; all ten moving cases must pass both sensing-only and recorded modes. Retain the original failing moving trajectory as an additional regression.
- Preserve the original planned final distance of 0.20–0.40 m, final-second speed below 0.01 m/s, no falls/contact, every actual scheduled pause settled and every departure resumed. The current 0.18 m lower limit is a legacy discrepancy, not permission to relax the next gate. Physical stopping must be measured beyond the STOP label. Faults retain the original next-tick veto and stopping requirements.
- Use identical guards. Learned inference must have zero teacher fallback, at least ten more successes than untrained across 50 episodes, and no more than two fewer than rules; report always-stop too. Require export parity, fresh-process load, fault checks, static/search and original coordinate regressions. Matching rules means learned/distilled behavior, not superior control.
- Before the experimentation cutoff, failure is a checkpoint: continue the next authorized diagnostic/correction without requesting a new prompt. Early completion requires all acceptance and publication gates. If a final failure prompts a repair, preserve it and use only the independently frozen reserve within remaining time; never tune and relabel the same test as unseen.
- At the deadline, finish privacy-reviewed closeout with PARTIAL if needed. Do not claim success or run indefinitely. A hard external blocker can end local progress earlier only after available recovery paths are exhausted. Record exact remaining work. A task/process interruption is not successful completion.
- If stages finish early, use the remaining experiment window for predeclared repeat seeds, latency/dropout or apparent-size sensitivity, reported separately from core acceptance. Do not idle to fill the clock. Keep machine-readable progress and meaningful stage/failure updates; resume checkpoints without duplicate jobs or publishing.

Next priorities are evaluation integrity and reliable following, then observation/history and latency robustness, then broader perception. General object recognition, obstacles/edges, new gait training and hardware remain out of scope.
