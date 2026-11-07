# SupeRR Scout · IPL 2027 auction lab

A lightweight, static scouting dashboard and data preparation path for the Rajasthan Royals SupeRR Selector challenge.

## What it does today

- Loads one or more player-summary CSV files locally in the browser. Files stay on the user's device.
- Filters to players age 25 or younger, using age or date of birth, and ranks a top 10 by role-aware T20 indicators, sample confidence, age upside and provisional squad fit.
- Shows source coverage and evidence confidence beside each player, and exports the current top 10 as CSV.
- Provides a public-source register and clearly marks the dashboard as pre-release until the proprietary pack arrives.

## Important model limitation

This is an explainable scoring baseline, not a trained probability model. The brief is not live until 8 Nov 2026 at 10:00 IST, and the data dictionary, eligible player pool, player-level outcomes and auction labels are not yet available. No honest system can claim pinpoint accuracy without those inputs and a time-separated backtest. Do not present score values as probabilities.

After the pack arrives:

1. Keep the original file unchanged and review its license and data dictionary.
2. Join on verified player identity, not name alone. Confirm dates of birth, uncapped status and role.
3. Add all available domestic T20 seasons, IPL history and auction outcomes. Exclude any post-cutoff data from training features.
4. Backtest by season (train on seasons before year `t`, rank candidates available in `t`, score subsequent IPL contribution) and report top-10 precision/recall, rank correlation, calibration, and uncertainty intervals.
5. Compare with a simple role-and-age baseline; retain the ML model only if it beats the baseline consistently.
6. Recalculate team-fit after RR's 2027 retention list, purse and overseas slots are known.

## Data inputs

The browser import expects a player-summary CSV with a name, age or DOB, role, uncapped status if supplied, and common batting/bowling summary fields. Recognized headings include `player`, `age`, `dob`, `team/state`, `role/specialism`, `matches`, `runs`, `balls faced`, `dismissals`, `strike rate`, `average`, `wickets`, `balls bowled`, `runs conceded`, `economy`, `dot balls`, `catches`, and `stumpings`. It accepts multiple CSV files. Do not upload proprietary files to a public web host.

## Reproducible public-data baseline

`train_model.py` trains a two-stage SMAT-to-next-IPL model from Cricsheet Ashwin CSV archives. It uses season-forward evaluation, a Cricsheet people/name registry join, an appearance classifier and an impact regression. The baseline is not a precision guarantee. See [the validation checkpoint](outputs/model_validation.md) for the holdout and fold results. `score_candidates.py` applies the saved model to a cleaned player-summary CSV; use its optional `--report` output to audit excluded rows. `work/data/` is the local data room for downloaded public archives and is intentionally not pushed to GitHub.

Example local commands:

```sh
python3 train_model.py --sma-zip work/data/sma_csv2.zip --ipl-zip work/data/ipl_csv2.zip \
  --people-csv work/data/people.csv --names-csv work/data/names.csv --out work/model
python3 score_candidates.py --model work/model/rr_scout_model.joblib \
  --input candidates.csv --output work/ranked_candidates.csv --report work/eligibility_audit.json
python3 benchmark_models.py
```

Cricsheet's experimental Ashwin CSVs are ball-by-ball, not player summaries. Aggregate them by player and season before browser upload; preserve competition and season fields and de-duplicate match/player rows. Do not mix formats or count an extra delivery as a legal ball unless the source says it is legal.

## Public sources to collect

- [Cricsheet downloads](https://cricsheet.org/downloads/) — IPL and Syed Mushtaq Ali Trophy match data, including ball-by-ball; review [format](https://cricsheet.org/format/) and [licensing](https://cricsheet.org/register/).
- [SMAT 2025–26 public scorecards](https://www.hycricket.in/data-2025-26/BCCI-matches/SMA-t20/) — player batting/bowling summaries.
- [BCCI 2026–27 domestic ready reckoner](https://documents.bcci.tv/bcci/documents/1779273276961_BCCI%202026-27%20Domestic%20Season%20Ready%20Reckoner.pdf) — competition schedule and structure.
- [IPL official statistics](https://www.iplt20.com/stats) — historical IPL results for context and validation.
- [Rajasthan Royals squad profiles](https://www.rajasthanroyals.com/rr-players) — role and roster context; re-check after 2027 retentions.
- [ESPNcricinfo records](https://www.espncricinfo.com/records) — independent bio and scorecard cross-checks.

## Run it

Open `index.html` in any modern browser. There is no build step or server. All ranking runs in the page and uploaded files are not sent anywhere.

## Scoring baseline

The browser's direct CSV import provides a transparent provisional heuristic (78% role skill, 12% age upside, 6% provisional role fit, 4% sample reliability). For the supervised two-stage outcome model, run `score_candidates.py` with the locally trained artifact and import its output CSV; the page will then use its 100-point model score and show the learned appearance probability. Validation is weak and documented in [model_validation.md](outputs/model_validation.md). Neither score estimates a 2027 auction success probability.

## Attribution

Attribute Cricsheet and any other public source used in derived files according to that source's terms. This dashboard itself bundles no third-party player data.
