# Working on the MicroDuck pet project

Read `PROJECT.md` before starting work. It records the owner's goals, decisions, current state, references, uncertainties, and next steps.

Update `PROJECT.md` when work changes a material decision, verified capability, project state, or next step. Date meaningful progress, preserve rationale, distinguish proposals from implemented and tested behavior, and record limitations. Keep the next concrete action near the top.

This is an independent personal repository for the agent layer. It is public; do not add secrets, absolute local paths, private personal details, or the owner's personal goals and context. Those live in the owner's local knowledge base, not here. The ignored `microduck-lab/` tree contains separate external Git repositories; do not add their source or histories to this repository. Read their own applicable instructions before any authorized work inside them.

Use the owner's current request to determine scope. Planned milestones in `PROJECT.md` do not by themselves authorize implementation, training, deployment, or other additional work.

The public-information boundary applies to code, documentation, comments, fixtures, logs, and commits. Do not include personal identities or household context, conversation transcripts, private KB content, personal machine paths/configuration, or credentials. Review the diff for private information before committing or publishing.

## Simulation iteration and media export

Separate camera sensing and visual validation from presentation export. During code/control iteration, do not mechanically encode an MP4 or GIF after every tweak. Keep the actual robot-camera RGB rendering required by image-based control and preserve scenario/test coverage. Render and inspect targeted frames or short clips when needed to diagnose a visual issue. Generate the user-facing recording after a meaningful verified result or an explicit request; reuse it for the final GIF when possible. Omitting an export must not mean omitting perception or necessary visual checks.

Plan a bounded sequence of related improvements together before execution. Keep the plan compact: dependencies, acceptance criteria, and failure branches. Spend a few minutes upfront when useful to avoid repeated planning between steps. Continue from the plan and replan only when evidence invalidates its assumptions; do not restart full planning or export media mechanically at each step. A proposed plan does not authorize its implementation.
