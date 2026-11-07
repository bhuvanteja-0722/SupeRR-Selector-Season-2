# Round 1 intake, scoring and export audit

**Checked 7 Nov 2026.** Round 1 is open 8 Nov 2026 10:00 a.m. IST through 18 Nov 2026 11:59 p.m. IST. The proprietary pack was not yet available during this check, so upload and ranking were exercised with disposable fixtures only. No sample player rows or proprietary data are included in GitHub. The local public evidence bundle contains 7,159 latest player/competition-season rows from 18 Cricsheet domestic/franchise T20 archives.

## Challenge-aligned workflow

1. Load the private pack locally after release. The file-level pack declaration is only for a challenge file that is confirmed to contain uncapped players but has no status column. Explicit capped status always wins. Capped, unknown, missing-name, invalid-age and no-performance-volume rows are not eligible.
2. There is no age ceiling in the supplied brief. The dashboard therefore applies no arbitrary under-26 cutoff; younger eligible players receive a higher relative youth score. Recheck pack rules when released.
3. Profile and public-performance rows can be separate. Public evidence joins only through a unique verified name/alias; ambiguous rows are held aside. Stable ID/DOB is preferred; name-only joins require review.
4. Exact duplicate rows are removed. Same-player records are reduced to the latest available season and same-season volumes are combined. Overlapping pack and public statistics are suppressed to avoid double counting.
5. The Round 1 top-10 scouting rubric ranks candidates using role-specific observed performance (60%), youth relative to eligible candidates (25%) and an explicitly selected provisional RR need scenario (15%). Batting compares strike rate, average, runs per match and batting-ball evidence depth. Bowling compares wicket rate, economy, dot-ball rate and bowling-ball evidence depth. Missing measures are omitted and remaining component weights are renormalized.
6. Each candidate displays why their evidence merits consideration, the rubric component scores, sample/identity/skill risks and separate historical IPL appearance model signals. Historical IPL model signals do not control the shortlist and are not auction probabilities. The RR scenario defaults to neutral pending official retentions/trades.
7. Export generates a top-10 CSV containing names, age, role, stats, score components, scenario, rationale and risk checks. The participant must review evidence and make their own submission decision.

## Checks performed

- Confirmed explicit uncapped, unknown-status, and capped semantics; only verified uncapped rows are eligible. Explicit capped status is not overridden by the pack declaration and capped profiles cannot be used to match public rows.
- Confirmed challenge-pack declaration admits a missing status only when enabled for the selected file; disabling it rejects the same row.
- Tested the visible Choose CSV files button end to end and tested dropping a second CSV onto the drop target; both added valid candidates and updated the dashboard.
- Confirmed the two dataset download links return HTTP 200 and `text/csv` over the local server.
- Confirmed public evidence preloads, stays held without a candidate profile, joins to one unique verified candidate, and avoids double counting overlapping pack/public stats.
- Checked duplicate handling, latest-season behavior, DOB parsing, inclusion of a 27-year-old because no upper age limit is stated, exclusion of the capped fixture, reason/risk generation, scenario-driven score change and top-10 CSV export fields.
- CLI scoring now has no maximum-age cutoff by default and uses the same 60/25/15 scouting rubric; an optional max-age can be supplied only if official rules require it. The PDF button calls browser print; print media styling shows the shortlist and methodology while hiding upload controls and dataset panels.
- Compiled changed Python files, checked dashboard JavaScript syntax and confirmed dashboard HTML copies match.

## Limits and interpretation

The public supervised model is a research aid trained to predict next-IPL appearance and a coarse impact proxy. Its latest broad chronological holdout was weak (ROC-AUC 0.539; top-10 hit rate 1/10); raw 96.2% accuracy merely matches the all-negative baseline. Historical DOB/uncapped labels are not sufficiently available to backtest this Round 1 eligible pool, and the 60/25/15 scouting weights are an explicit heuristic, not learned or proven optimal. RR's official 2027 retentions were not yet published. Update role priorities from the pack, confirmed roster and permitted public sources, inspect original scorecards, manually verify identities, and retain human judgment. Keep the proprietary pack private and out of GitHub.
