# SupeRR Scout model checkpoint

**As of 7 Nov 2026.** The 8 Nov challenge pack is not live yet. No 2027 candidate ranking is being reported.

## What was trained

An explainable two-stage model using public Cricsheet Syed Mushtaq Ali Trophy (SMAT) player-season summaries as features and the immediately following IPL season as the outcome:

1. Logistic regression estimates whether a player appeared in the next IPL season.
2. Ridge regression estimates per-match impact among players who appeared, using `(runs + 20 × wickets) / IPL matches`.
3. Expected impact is `appearance probability × predicted per-match impact`.

The final candidate score blends expected-impact percentile (70%), age percentile (20%) and provisional RR role fit (10%). Age and role fit are applied when the challenge candidate file is scored; they are not learned from this historical model.

Training uses 3,851 player-season rows from eight SMAT seasons (2015/16 and 2017/18 through 2023/24). Identity matching uses Cricsheet's people and name-variant registers; ambiguous variants are not automatically merged. Candidate names still require manual identity checks.

## Validation

The latest season is held out in full: SMAT 2024/25 profiles predict IPL 2025 outcomes (102 player rows). Earlier seasons are used for fitting.

| Measure | Holdout result | Readout |
|---|---:|---|
| Accuracy at 0.50 probability | 64.7% | Same as predicting that no player appears |
| ROC-AUC | 0.662 | Some ranking signal, far below a high-confidence model |
| Top-10 precision for next IPL appearance | 50% (5/10) | Four of the ten ranked players did not appear |
| Brier score | 0.276 | Worse than the 0.228 prevalence-only baseline |
| Impact MAE among players who appeared | 9.88 | Error in the runs-plus-wickets per-match label |

Walk-forward evaluation trains on earlier seasons and validates on each later season. Across five folds the mean AUC is 0.722 and mean top-10 appearance precision is 58%; fold precision ranges from 30% to 100%. The latest season is small and weaker than the earlier folds. This is not stable evidence for 95% accuracy.

Four classifier families were compared with the same five season-forward folds. Logistic regression was retained because it had the best average AUC (0.722) and top-10 precision (0.58). Random forest averaged 0.708 AUC / 0.52 top-10 precision; extra trees 0.712 / 0.58; histogram gradient boosting 0.717 / 0.52. None approaches 95%, and the 2025 holdout remains the most relevant and weakest fold.

## Why 95% cannot be claimed

“Accuracy” depends on the outcome being predicted. Here the available public data only lets us predict next-season IPL appearance and a coarse impact measure. It does not label whether RR should have bought a player, whether a bid would succeed, or whether that player would improve RR in 2027. The 2025 holdout does not support 95% accuracy, and the appearance probability is not well calibrated. A 95% target should remain a validation goal, not a promised result.

The SMAT archive includes 695 of 1,205 listed matches (57.68%); missing match coverage can bias the player pool and aggregate rates. The model also lacks age, injury, role-at-phase, venue, auction price, trials/scouting notes, RR retention needs and the proprietary pack's own fields. Those omissions matter for a franchise shortlist.

## Next validation step after the pack arrives

- Inspect the brief, data dictionary and permitted uses before loading it.
- Resolve player names to stable IDs and manually verify every shortlisted player's DOB, uncapped status and role.
- Join the private domestic data to the public T20 evidence without mixing seasons or double-counting players.
- Refit/backtest by season, compare against role-and-age baselines, and report top-10 precision/recall, rank correlation and calibration with confidence intervals.
- Adjust role-fit weights only after 2027 RR retentions, purse and squad gaps are known.
- Report a final top 10 only after those checks. Keep model output separate from scout judgement and explain the strongest counter-evidence for each pick.

## Sources and attribution

- [Cricsheet downloads](https://cricsheet.org/downloads/) and [coverage](https://cricsheet.org/coverage/): IPL and SMAT ball-by-ball archives; SMAT coverage is listed as 695/1,205 matches.
- [Cricsheet people/name register](https://cricsheet.org/register/): identity matching and name variations.
- [Cricsheet licensing](https://cricsheet.org/licensing/): follow ODC-BY attribution for derived data.
- [BCCI domestic season ready reckoner](https://documents.bcci.tv/bcci/documents/1779273276961_BCCI%202026-27%20Domestic%20Season%20Ready%20Reckoner.pdf).
- [Rajasthan Royals player profiles](https://www.rajasthanroyals.com/rr-players) and [IPL official stats](https://www.iplt20.com/stats) for current role/roster context and public cross-checks.

Raw public archives are kept outside this repository. The trained model and aggregate metrics are generated locally with `train_model.py`.
