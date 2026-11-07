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

Within-role percentiles combine batting strike rate, average and run volume (44/30/26) or bowling wicket rate, economy and dot-ball rate (48/35/17). The skill estimate is shrunk toward a neutral score according to match count; an initial confidence factor is `matches / (matches + 5)`. The overall blend is 78% skill, 12% age upside, 6% provisional role fit and 4% evidence reliability. All weights are explicit and should be replaced or tuned only after backtesting. The current web implementation does not estimate phase-specific skills, venue effects or a learned outcome probability.

## Attribution

Attribute Cricsheet and any other public source used in derived files according to that source's terms. This dashboard itself bundles no third-party player data.
