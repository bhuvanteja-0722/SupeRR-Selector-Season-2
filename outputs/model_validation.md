# SupeRR Scout validation report

**Updated 7 Nov 2026.** The challenge pack releases 8 Nov; no 2027 shortlist is generated until that pack is loaded and checked.

## Training data and method

A two-stage, interpretable baseline was trained on **19,231 player-season records** built from 18 Cricsheet domestic/franchise T20 archives. It learns next-IPL-season appearance with logistic regression and conditional per-match contribution with Ridge regression. The impact label is `(runs + 20 × wickets) / IPL matches`; expected contribution multiplies predicted impact by appearance probability. Historical IPL seasons supply labels.

Archives used: sma_csv2.zip, bbl_csv2.zip, bpl_csv2.zip, cpl_csv2.zip, ctc_csv2.zip, etpl_male_csv2.zip, ilt_csv2.zip, ipt_male_csv2.zip, lpl_csv2.zip, mct_male_csv2.zip, mlc_csv2.zip, msl_male_csv2.zip, npl_male_csv2.zip, ntb_male_csv2.zip, pro20_male_csv2.zip, psl_csv2.zip, sat_csv2.zip, ssm_male_csv2.zip. Men's T20I and World Cup archives, plus Cricsheet people/name registers, are retained as identity and research resources; T20I data is not treated as domestic franchise evidence. Competition-season rows remain distinct, ambiguous player name variants are not automatically merged. Features are batting/bowling volume and rates plus coarse role indicators; age and RR squad fit are downstream shortlist factors, not learned outcomes.

## Latest forward holdout

The most recent eligible competition-season in the archived data is **ssm_male:2025/26**, mapped to IPL **2026**. This holdout has 106 player rows and an appearance rate of 3.8%.

| Measure | Result | Interpretation |
|---|---:|---|
| Raw accuracy at 0.50 | 96.2% | Exactly the all-negative baseline (96.2%); not evidence of useful prediction |
| ROC-AUC | 0.588 | Weak ranking signal on this holdout |
| Top-10 appearance precision | 10% | 1/10 selected players appeared |
| Brier score | 0.043 | Worse than prevalence-only baseline (0.036) |
| Walk-forward mean AUC | 0.692 | Mean over 124 competition-season folds; repeated IPL target seasons and heterogeneous leagues make this descriptive, not independent evidence |
| Walk-forward mean top-10 precision | 24.6% | Low shortlist hit rate across the folds |

## Decision

The larger pool does **not** make this a pinpoint model. Accuracy is misleading under the rare appearance label: predicting no one appears reaches the same holdout accuracy. The latest AUC, top-10 hit rate and Brier score show this model is unsuitable as a decision-maker. Use it only to organize evidence, then combine the challenge pack, verified age/uncapped status, role needs, workload, venue/phase skills, auction constraints and human scouting. No claim of 95% accuracy is supported.

## Data limits and next update

Cricsheet coverage is incomplete and varies by competition; league strength and player pools differ. Name resolution is imperfect. The target (any next-season IPL appearance) is not the same as RR purchase or player value to RR. Cross-league rows for the same person can appear in separate competition seasons; this evaluates transferability but does not mean the rows are independent. The 2026 season can have incomplete availability in archives.

When the pack arrives: confirm its permitted use and schema, join candidates to stable identities, verify DOB/uncapped status, de-duplicate seasons, compare age-role baselines with the model in chronological backtests, calibrate probabilities, inspect errors and uncertainty, then produce a sourced top 10.

## Sources and attribution

- [Cricsheet downloads](https://cricsheet.org/downloads/) and [coverage](https://cricsheet.org/coverage/) — public ball-by-ball archives.
- [Cricsheet registers](https://cricsheet.org/register/) — people and name variants.
- [Cricsheet licensing](https://cricsheet.org/licensing/) — Open Data Commons Attribution terms; retain source and attribution when redistributing.
- [Rajasthan Royals official squad](https://www.rajasthanroyals.com/rr-players) — dashboard uses linked official squad portraits and logo.

## Rajasthan Royals roster context (checked 7 Nov 2026)

The latest official roster page is labelled **IPL 2026**, so it is a reference squad, not a confirmed 2027 retention list. In the completed 2026 trades, RR sent Sanju Samson to CSK for Ravindra Jadeja and Sam Curran; Nitish Rana moved to DC and Donovan Ferreira came to RR. The official IPL notice confirms the named 2026 transfers. The official RR 2026 squad page also records replacement players, so it should not be mistaken for an unchanged 2027 contract list.

On 6 Nov, Cricbuzz reported RR–LSG trade talks, saying RR were seeking a fast bowler who had a successful LSG stint, an LSG spinner could also be included, and RR might send a batter and perhaps an all-rounder. The article explicitly said the deal had not gone through and did not disclose names. Treat this as a **scenario only**, not a completed deal or confirmed player movement. Do not assign a particular player to either side from that report.

RR's 2026 batting form was strong at the top: Vaibhav Sooryavanshi made 776 runs in 16 matches (48.50 average, 237.30 strike rate); Dhruv Jurel 515 (36.79, 154.65); Yashasvi Jaiswal 427 (30.50, 152.50). Together: 1,718 runs. Official RR's page says the team won its first four games and reached Qualifier 2. The same top three already cover major batting roles, so an assumed batter exit should be replaced according to the exact slot lost; do not automatically add another opener.

Team phase comparison, calculated from Cricsheet IPL Ashwin deliveries (runs conceded by RR per six legal balls; rankings are worst to best among the 10 teams):

| Phase | 2025 RR rate / rank | 2026 RR rate / rank | Readout |
|---|---:|---:|---|
| Powerplay bowling | 9.41 / 6th | 10.43 / 4th | Small deterioration; seek control only if the player pool and final squad justify it |
| Middle-over bowling | 9.58 / 2nd | 9.57 / 6th | Nearly flat rate; wicket/role context matters |
| Death bowling | 12.71 / 1st | 11.06 / 5th | Large improvement; still a monitoring area, not an automatic emergency |
| Powerplay batting strike rate | 181.7 | 194.4 | Strong phase; avoid over-weighting another opener by default |
| Middle-over batting strike rate | 145.4 | 159.4 | Improved; check spin matchup quality and sample before acting |
| Death-over batting strike rate | 175.0 | 177.1 | Similar, with role-specific depth still dependent on who is retained/traded |

### Auction role suggestions by trade scenario

- **If the RR–LSG rumour completes as reported:** assume RR gain an LSG pacer and potentially a spinner, while at least one batter may leave and an all-rounder may be part of the exchange. Lower pace/spin auction priority if the incoming players are contracted and available. Target a young uncapped Indian middle-order finisher who handles spin and has a defensible death-phase batting record. Add a two-skill all-rounder only if RR lose one without an equivalent coming in. If the batter leaving is an opener, replace that role specifically; names remain unknown.
- **If no trade happens:** retain death-phase / powerplay bowling control as a secondary need (not a blanket “buy any fast bowler” signal), and prioritize young Indian batting depth or finishing only if retentions create a gap.
- **For either case:** score actual candidates on 2025 and 2026 form, phase splits, opponent/venue context, role, sample size, availability, age, uncapped status and auction price. The challenge pack and official 2027 retained/released list may change all priorities.

The complete 2025–26 reference squad and player-level form rows are in [rr_squad_form_2025_2026.csv](rr_squad_form_2025_2026.csv); blank rows mean the Cricsheet register did not resolve a player ID, not zero ability. Performance is IPL-season ball-by-ball and should be cross-checked against official scorecards. The assumptions and conditional roles are detailed in [rr_auction_scenarios.md](rr_auction_scenarios.md).

Official/current sources: [RR 2026 squad](https://www.rajasthanroyals.com/rr-players), [IPL official 2026 trade notice](https://www.iplt20.com/news/article/tata-ipl-2026-player-trade-updates), [RR 2026 stats](https://www.rajasthanroyals.com/stats), [RR 2026 season summary](https://www.rajasthanroyals.com/latest-news/rr-indian-premier-league-ipl-2026-top-run-scorers), [Cricbuzz 6 Nov RR–LSG report](https://www.cricbuzz.com/cricket-news/140807/mega-lsg-rr-trade-in-the-offing), [official IPL news index](https://www.iplt20.com/news).
