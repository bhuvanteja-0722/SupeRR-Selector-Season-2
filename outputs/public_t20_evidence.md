# Public domestic T20 evidence bundle

`public_t20_evidence.csv` contains 7,159 player/competition rows, one latest available season per player in each of 18 Cricsheet domestic/franchise T20 archives. The bundle includes player names, register IDs and aliases where resolvable, competition and season, matches/innings, batting and bowling volume, rates and dot balls. It does not include age, uncapped status, or RR evaluation.

The dashboard loads this file automatically when opened over HTTP from the project root. It keeps unmatched evidence on hold; after the uncapped-only challenge pack is uploaded, public rows join only to one uniquely verified candidate name/alias. When a stable Cricsheet ID is unavailable, identity is name-based and the dashboard marks it for verification. Public evidence rows with no candidate match never appear in the shortlist.

Regenerate with `python3 build_public_t20_evidence.py --data-dir work/data --out outputs/public_t20_evidence.csv`. Source archives and registers are covered by Cricsheet's ODC-BY license; preserve attribution and review the source terms at [Cricsheet licensing](https://cricsheet.org/licensing/). Archive-level inventory is in `dataset_inventory.csv` and notices are in `work/data/ATTRIBUTION.md`.
