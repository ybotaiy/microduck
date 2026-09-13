# Image-only ball following — September 12, 2026

`--vision --dual-view` connects actual uncompressed `robot_view` RGB frames to the existing walking and standing policies. The detector chooses the largest connected magenta region; its horizontal centroid controls yaw and apparent bounding-box diameter controls stopping. It rejects tiny or image-edge-clipped components. No target coordinates, depth, segmentation IDs, or scripted trajectory enter `VisionFollower.command`.

The camera runs at 25 simulated frames per second; the existing policy runs at 50 Hz. Missing or stale frames cause zero forward/yaw commands. Size hysteresis uses diameter/image-height thresholds 0.17 to stop and 0.14 to resume, with a 0.8-second restart dwell. These are empirical image thresholds for this virtual camera and ball, not calibrated distance estimates. Existing proprioceptive policy observations remain unchanged. Ground-truth pose, ball coordinates and segmentation are used only by the environment/evaluator and third-person presentation.

## Reproduction

Use the environment described in `SIMULATION.md`, from the repository root:

```bash
microduck-lab/.venv/bin/python sim/experiment.py --mode ball --ball 0.8 0.35 \
  --seconds 18 --video --dual-view --vision --out runs/vision-static
microduck-lab/.venv/bin/python sim/experiment.py --mode follow --ball 0.6 0.05 \
  --seconds 42 --video --dual-view --vision --out runs/vision-follow
microduck-lab/.venv/bin/python sim/experiment.py --mode ball --ball 0.8 0.35 \
  --seconds 18 --video --dual-view --vision --vision-blackout 4 6 --out runs/vision-blackout
microduck-lab/.venv/bin/python sim/check_vision_run.py runs/vision-follow
microduck-lab/.venv/bin/python -m unittest discover -s sim -p 'test_*.py'
```

## Measured outcomes

| Test | Result |
| --- | --- |
| Stationary left-front ball, 18 s | Stopped at 0.3042 m; no fall/contact; no missed visible ball in 90 evaluator samples. |
| Existing moving/pausing trajectory, 42 s | Resumed after both departures and settled in all three pauses; final distance 0.2701 m, minimum 0.2572 m, maximum after first stop 0.4271 m; no fall/contact. |
| Dynamic perception limitation | A 0.40 s loss occurred at t=30.08–30.48 while stopping. Zero commands throughout. Two of 210 sampled evaluator frames contained visible ball pixels without an accepted detection. This run passes its behavioral criteria, but is not flawless tracking. |
| Injected black camera frames, t=4–6 s | Immediate zero commands during blackout, passive reacquisition afterward, final stop at 0.3086 m; no fall/contact. This is an injected sensor failure, not a physical occluder. |
| Initially out-of-view ball, 6 s, search disabled | Stayed lost with zero commands; correctly did not approach. This is a lost-sight check, not an approach success. |
| Coordinate baseline regression | All original fields in 900 stationary and 2,100 moving-target samples exactly match the prior runs. |
| Image-command replay | Recorded commands reproduce exactly from image features and timestamps alone for stationary, moving, blackout and out-of-view tests. |

The initial moving-target trial used a later stop-size threshold (0.20). It failed the first hold: post-command body motion brought the ball too close, then it was clipped at the image boundary and rejected. The failed recording is retained. The final threshold triggers stopping earlier; stopping a policy is not an instantaneous halt of the simulated body.

Rendered segmentation checks run at 5 simulated Hz and cannot prove correctness between samples. This simple detector is specific to the controlled magenta-ball scene; it has not been validated against same-colored distractors, arbitrary lighting, real cameras or hardware. XML position actuators are used, not BAM. No retraining occurred.

## Active search extension

This paragraph records the first search iteration. The subsequent bounded yaw=1.2 rear-search success is documented in `BOUNDED_SEARCH.md`.

The opt-in `--search` extension has now been tested. Left/right active head search and recovery after removal of an opaque wall passed; behind-target reacquisition failed and stopped at its scan time limit. It uses a head-joint encoder in addition to RGB detections and timing, never ball/world coordinates. See `VISUAL_SEARCH.md` for commands, evidence, and limitations. Passive blackout recovery above is not active search.
