# Proposed roadmap

This roadmap is planning only. It does not authorize new experiments, training or deployment. The goal is coherent pet-like interaction, not increasingly advanced stunts. Use one compact plan per authorized sequence, replan only when evidence invalidates assumptions, time the phases, and export presentation media only when useful.

| Proposed step and dependency | Acceptance evidence | Failure branch |
| --- | --- | --- |
| 1. Preserve the current foundation | Bounded turning/search, action outcomes, baselines and representative media remain reproducible. | Stop regression and resolve it before adding behaviors. |
| 2. Characterize sensing and actions, after foundation | Measure camera blind spots, observable obstacle/edge distance, stopping margin, action completion/failure/timeouts, and interruption behavior. | Mark unobservable or unreliable cases unsupported; do not infer safety from RGB alone. |
| 3. Independent motion veto, after measured sensing | In known simulated layouts with realistic sensors, veto/stop on obstacles, edges, stale/invalid sensors or uncertainty. Ground truth is evaluator-only. | Stop on insufficient evidence; add sensing or reduce the operating envelope. |
| 4. Local detour/replan, after veto tests | Navigate simple known safe terrain; test dynamic obstacles and simulated people/pets, with blocked-path timeout. | Wait or stop; do not indefinitely push toward a blocked target. |
| 5. Coherent interaction, after safe actions | Explicit rules baseline for attention, waiting, following, disengagement and user stop; action feedback prevents overlapping or unfinished behaviors. | Return to a neutral stopped state; do not interpret attention as enjoyment. |
| 6. Train only measured missing skills | Establish a specific low-level deficit and compare a trained skill against the existing policy and a trivial baseline. | Keep existing skills; no training merely to make demonstrations more elaborate. |
| 7. Staged hardware and participant evaluation | Floor-level supervised trials, explicit manual stop, bounded speed/contact, then participant feedback. Preserve the simulation/hardware gap. | Stop and reassess any unsupported sensor/action assumption. |

Across stages, propose repeated seeds/layouts, lighting and same-color distractors, sensor latency/failure, stopping distances, camera blind spots, action interruption, speed/contact limits and manual stop. Passing one deterministic simulation is not permission to skip these checks. Keep participant identities and private context outside this public repository.
