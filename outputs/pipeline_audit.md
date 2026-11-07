# Upload, preprocessing and scoring audit

**Checked 7 Nov 2026.** The 8 Nov proprietary pack was not yet available during this check, so the upload workflow was exercised with disposable sample CSVs. No sample player rows are included in the repository. A public evidence bundle was generated from 18 Cricsheet domestic/franchise T20 archives: 7,159 latest player/competition-season rows. It preloads when the dashboard runs over HTTP.

## What happens after upload

1. The browser parses quoted CSV rows, normalizes headers and recognizes player, age/DOB, team, role, cap status, season and batting/bowling fields.
2. Exact duplicate rows are removed. Rows explicitly marked capped are excluded. Missing/ambiguous cap status is excluded unless it can be joined by a unique name/alias to one explicitly uncapped profile, or the user marks selected files as the official uncapped-only challenge pack. An explicit capped label always overrides the pack declaration, including during profile matching. That declaration is stored per file; turn it off before adding public evidence.
3. A valid age is calculated from DOB when necessary, using 8 Nov 2026 as the auction reference. Players outside age 0–25 are excluded. Rows without batting or bowling volume are excluded.
4. Profiles and performance summaries can be uploaded in separate CSVs. Bundled public rows join only to one uniquely verified player name or alias; names that match multiple profiles are held aside. A stable player ID or DOB is preferred. Without either, the fallback is normalized name plus team, and Cricsheet name-only matches are flagged for human identity review.
5. For one player, multiple rows from the latest season are combined by volume and rates are recalculated. Older-season rows are ignored for ranking. The on-page audit reports rows, eligibility exclusions, joined rows, exact duplicates, and older rows ignored.
6. The browser builds the same 12 features as the trained models and runs both the multi-league and SMAT logistic/Ridge models locally. Their expected-impact ranks are blended 50/50; the final score weights blended rank 70%, age 20%, and provisional RR role fit 10%. CSV export includes both model signals, expected impacts, rank blend, score, season and evidence volume.

## Data-preparation correction

The training pipeline previously counted only the first batter as having an innings in each team innings. It now counts each batter's innings separately. Dismissal matching now compares resolved player identifiers consistently. The public-data baseline was retrained after these corrections. Corrected results are in `holdout_metrics.json`; candidate ranking experiments are in `hit_rate_benchmark.json`.

## Checks performed

- Parsed a verified uncapped candidate, an unknown-status row, and a capped-status row. Only verified uncapped entries remained eligible.
- Uploaded profile and statistics files separately. The statistics row joined to its unique verified profile and inherited DOB/age and team.
- Tested the visible “Choose CSV files” button end to end: selecting a valid CSV added one eligible uncapped player and updated the audit. Tested dropping a second CSV into the drop zone: the second candidate appeared, taking the count to two.
- Checked both new dashboard dataset download links over the local server; each returned HTTP 200 with `text/csv` (prepared evidence bundle and dataset inventory).
- Confirmed an explicitly capped player never becomes a public-join profile, even if the capped row came from a file marked as the uncapped-only pack.
- Confirmed the bundled public evidence preloads (7,159 rows) and stays on hold before candidate profiles arrive. Marked a sample uncapped pack profile at upload time, then verified that only its matching latest-season public row joined and scored; unmatched public players stayed held aside.
- Uploaded same-player rows from two seasons. Latest-season volumes combined and the older-season row was excluded from scoring.
- Used the challenge-pack declaration with a file that had no cap-status column; the row entered the shortlist. The same row is rejected when the declaration is off.
- Checked generated multi-model signal values against scikit-learn inference for the same feature vector; displayed rounded signals agreed.
- Exercised the top-10 CSV export and confirmed it contains the current score fields and season.
- Confirmed CLI scoring excludes missing cap status by default and excludes capped rows even when `--pack-uncapped` is enabled.
- Compiled changed Python files, checked dashboard JavaScript syntax and confirmed the two dashboard HTML copies match.

## Limits

The strongest top-10 result remains a small chronological SMAT backtest: the fixed blend averaged 6/10 across five folds versus 5.4/10 for multi-league expected impact. It hit 6/10 on the latest fold while the multi-league ranker hit 7/10. This is an encouraging but preliminary change in an indirect historical target—whether a player appeared in the next IPL—not RR auction success or player value. The five-fold validation includes all SMAT players; historical DOB/cap labels were not consistently available to replay the dashboard’s under-26, uncapped filter, so this gain has not been verified on that filtered pool.

The latest broad holdout remains weak (1/10 top-10 precision and ROC-AUC 0.539). Probabilities are not calibrated and are labeled as signals. RR's 2027 retention list was not published at audit time, so role fit is only a provisional 2026 reference. The challenge pack, source permissions, stable player identities, exact age/cap eligibility, role-specific phase data and official 2027 roster must be checked before a top 10 is treated as a recommendation. Multi-season summaries are reduced to the latest season; match-by-match form and venue/opponent adjustments are not inferred when the uploaded pack does not contain those fields. Name-only public evidence matches require manual identity confirmation.
