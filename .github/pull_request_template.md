<!--
  One PR does one thing. If the description needs an "and", it is probably two PRs.

  The full rules live in CONTRIBUTING.md — this template only asks for the parts
  that are easy to forget.
-->

### What this PR changes

<!-- One or two sentences. What is different after this merges? -->

### Why

<!--
  The problem, not the solution. If this fixes an issue, say which one
  ("Fixes #123").
-->

### How it was verified

<!--
  Which gates you ran, and what you saw. A gate that was not run is a gate that
  did not pass — so name the ones you did not run, too.

  The full gate list is in docs/internal/FACTS.md § 2.
-->

- [ ] Full regression suite (`python regress.py`)
- [ ] The self-hosting closure still holds (`make` iterates to a fixed point)
- [ ] Documentation touched is fact-checked against the current source

### Notes for the reviewer

<!--
  Anything that makes review faster: the parts you are unsure about, the
  trade-offs you made, the corners you deliberately left alone.

  If this changes compiler sources, say so explicitly — it costs a release-grade
  process (see CONTRIBUTING.md), and the reviewer needs to know before merging.
-->

- [ ] This changes `compiler/src0/*.jhyy` (release-grade process applies)
- [ ] This changes only documentation / scripts / templates
