# SupeRR Scout · IPL 2027 auction lab

A lightweight Rajasthan Royals themed scouting dashboard and reproducible public-data research baseline. It is ready for the 8 Nov challenge pack, which is not included yet. The current model is not accurate enough to make picks by itself and does not support a 95% useful-accuracy claim.

## Current state

- The static dashboard is in `index.html`; `outputs/superrr-scout-dashboard.html` is the same deliverable. It preloads a local Cricsheet evidence bundle on HTTP and imports candidate CSVs in the browser; uploaded data remains on the device.
- Candidate intake requires a valid age or DOB. Capped rows are excluded; unknown-status stats can join only one unique verified profile. If the official challenge pack has no cap-status column, use the pack-only declaration, and only for that uncapped-only pack. The source season and row-quality audit are visible.
- The dashboard public-data section includes direct CSV downloads for `outputs/public_t20_evidence.csv` (7,159 latest player/competition seasons) and `outputs/dataset_inventory.csv` (source links and coverage), in addition to source pages. The dashboard preloads it, keeps unmatched rows on hold, and joins public evidence to verified challenge-pack names/aliases only when the match is unique. Name-only identity rows are flagged for review.
- The dashboard combines same-season rows for the same player, removes exact duplicates, and ranks only the latest season found for that player. It displays the row-quality audit before export. Mark pack files as the uncapped-only source before adding them, then turn the declaration off before adding public files.
- `train_model.py` trains a two-stage model on 18 domestic/franchise T20 archives, with IPL outcomes, Cricsheet identities and chronological validation. The latest validation has 19,231 training player-season rows, 0.539 ROC-AUC, and 1/10 top-10 appearance precision. Its 96.2% raw accuracy is exactly the all-negative baseline. See `outputs/model_validation.md`.
- `build_rr_roster_form.py` creates `outputs/rr_squad_form_2025_2026.csv`, joining the official RR 2026 squad categories with IPL 2025/2026 ball-by-ball form where identity matches. Empty cells mean unresolved or unavailable evidence.
- `outputs/rr_auction_scenarios.md` compares RR phase performance and sets conditional role priorities if the reported RR–LSG trade happens or falls through. The rumour names no players and is not treated as a completed trade.
- `outputs/rr_scout_model.joblib`, `outputs/rr_scout_model_smat.joblib`, `outputs/model_inference.json`, `outputs/holdout_metrics.json`, `outputs/latest_season_holdout.csv` and `outputs/dataset_inventory.csv` preserve trained artifacts and research output.
- The upload runs both trained models directly in the browser and ranks by their fixed 50/50 expected-impact rank blend, then age and provisional RR fit. In five chronological SMAT folds this blend averaged 6/10, compared with 5.4/10 for multi-league alone; on the latest fold it scored 6/10 versus 7/10. Treat this small-sample gain as preliminary.
- `benchmark_scouting.py` compares ranking approaches on five chronological SMAT folds; the fixed rank blend is the dashboard default pending validation on the challenge pool. See `outputs/hit_rate_benchmark.json` and `outputs/model_validation.md`.
- `outputs/pipeline_audit.md` documents CSV preprocessing, cap-status handling, public-data joins, scoring, export and the workflow checks performed. `outputs/public_t20_evidence.md` describes the public bundle and attribution.

## Run locally

Run `python3 -m http.server 8765` from the project root and open `http://127.0.0.1:8765/`; this loads the bundled public evidence automatically. Opening the HTML directly also works, but the public bundle must then be selected manually. To retrain the broad public baseline from the included archives:

```sh
python3 train_model.py --domestic-zips work/data/sma_csv2.zip work/data/bbl_csv2.zip work/data/bpl_csv2.zip work/data/cpl_csv2.zip work/data/ctc_csv2.zip work/data/etpl_male_csv2.zip work/data/ilt_csv2.zip work/data/ipt_male_csv2.zip work/data/lpl_csv2.zip work/data/mct_male_csv2.zip work/data/mlc_csv2.zip work/data/msl_male_csv2.zip work/data/npl_male_csv2.zip work/data/ntb_male_csv2.zip work/data/pro20_male_csv2.zip work/data/psl_csv2.zip work/data/sat_csv2.zip work/data/ssm_male_csv2.zip --ipl-zip work/data/ipl_csv2.zip --people-csv work/data/people.csv --names-csv work/data/names.csv --out work/model
python3 build_public_t20_evidence.py --data-dir work/data --out outputs/public_t20_evidence.csv
python3 train_model.py --sma-zip work/data/sma_csv2.zip --ipl-zip work/data/ipl_csv2.zip --people-csv work/data/people.csv --names-csv work/data/names.csv --out work/model_sma
python3 export_model_params.py --multi work/model/rr_scout_model.joblib --smat work/model_sma/rr_scout_model.joblib --out outputs/model_inference.json --dashboard index.html --mirror outputs/superrr-scout-dashboard.html
python3 score_candidates.py --model work/model/rr_scout_model.joblib --secondary-model work/model_sma/rr_scout_model.joblib --input candidates.csv --output work/ranked_candidates.csv --report work/eligibility_audit.json
```

Candidate rows need verified names/IDs, DOB/age, role, uncapped status and domestic T20 performance. If the official pack contains only uncapped players but has no status column, add `--pack-uncapped` to the scoring command; use it only when the entire file is that official pack. Review the challenge brief and data permissions before use; keep the original pack unchanged. Do not publish the proprietary pack. Refit and evaluate against role/age baselines after adding the pack and checking the official RR 2027 retained, released and traded list.

## Public data and attribution

`work/data/` contains the downloaded Cricsheet Ashwin CSV archives and people/name registers. See `work/data/ATTRIBUTION.md` and `outputs/dataset_inventory.csv` for direct sources, competition coverage, intended use and ODC-BY attribution. Men's international and T20 World Cup archives are research references, not model feature inputs. The repo contains no proprietary Rajasthan Royals challenge data.

The dashboard's RR logo and player portraits link to the official [Rajasthan Royals squad page](https://www.rajasthanroyals.com/rr-players). Current squad/trade statements and form context are linked in the validation and scenario reports.

## Data boundaries

Cricsheet match coverage varies, identity joins are imperfect, franchise-strength differences matter, and separate league-season rows for one player are not independent observations. The trained target is next-IPL appearance and a coarse impact label, not RR purchase success or a 2027 performance. The current score is a research aid; wait for the pack and confirmed 2027 team context before publishing a named top 10.
