# Evidence Scope

This repository does not mirror the entire `ACM_Project/research_assets/` tree.

For the second paper, we include the evidence chain required to support the
public audit narrative:

## Included

- full-sample pathology audit
- full-sample pathology summary outputs
- pathology map figure
- resistant-sample metadata table
- distance-edge audit outputs
- stellar-normalization (`M/L`) audit outputs
- hard31 gas-shape and geometry audit outputs
- raw `Vgas` spectrum comparison outputs
- the script snapshots that generate the main paper-II audit chain
- the archived operator scripts referenced by Appendix A

## Excluded From Core Evidence

These are preserved in the research workspace but are not part of the core
public evidence package:

- failed operator sweeps
- intermediate negative-result tables not needed by the paper narrative
- exploratory assets that are useful for research history but not required for
  public reproduction

## Principle

The public second-paper codebase should expose:

- the stable retained galaxy trunk
- the audit evidence tables used in the paper
- the frontend bundle generation path
- the audit-process scripts needed to understand how those tables were produced

without turning into a dump of the entire research kitchen.
