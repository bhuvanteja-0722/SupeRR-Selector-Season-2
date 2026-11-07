#!/usr/bin/env python3
"""Forward-validate shortlist ranking on Indian SMAT candidate pools.

Compares a SMAT-only ranker, a broader multi-league ranker, and a fixed 50/50
rank-percentile blend. This is a small-sample decision aid, not a model-selection
guarantee. The final SMAT season is reported separately as the latest holdout.
"""
import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from train_model import (FEATURES, aggregate, build_frame, combine, fit_models,
                         load_deliveries, load_name_registry, predictions,
                         season_bounds)

DEFAULT_DOMESTIC = [
    "sma_csv2.zip", "bbl_csv2.zip", "bpl_csv2.zip", "cpl_csv2.zip",
    "ctc_csv2.zip", "etpl_male_csv2.zip", "ilt_csv2.zip",
    "ipt_male_csv2.zip", "lpl_csv2.zip", "mct_male_csv2.zip",
    "mlc_csv2.zip", "msl_male_csv2.zip", "npl_male_csv2.zip",
    "ntb_male_csv2.zip", "pro20_male_csv2.zip", "psl_csv2.zip",
    "sat_csv2.zip", "ssm_male_csv2.zip",
]


def rank_percentile(values):
    order = np.argsort(np.asarray(values), kind="mergesort")
    out = np.zeros(len(order), dtype=float)
    if len(order) > 1:
        out[order] = np.arange(len(order), dtype=float) / (len(order) - 1)
    return out


def precision_at_10(labels, scores):
    n = min(10, len(labels))
    indices = np.argsort(-np.asarray(scores), kind="mergesort")[:n]
    return float(np.mean(np.asarray(labels)[indices])) if n else None


def fit_recency_weighted(rows, ends, cutoff, half_life):
    """Fit same baseline while exponentially down-weighting older seasons."""
    x = np.asarray([[r[f] for f in FEATURES] for r in rows], dtype=float)
    y = np.asarray([r["ipl_next_appearance"] for r in rows], dtype=int)
    cutoff_date = date.fromisoformat(cutoff)
    years = np.asarray([max(0.0, (cutoff_date - date.fromisoformat(ends[r["domestic_season"]][1])).days / 365.25)
                        for r in rows])
    weights = np.exp(-np.log(2) * years / half_life)
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=.35, max_iter=2000))
    clf.fit(x, y, logisticregression__sample_weight=weights)
    appeared = [i for i, r in enumerate(rows) if r["ipl_next_appearance"]]
    rx = x[appeared]
    ry = np.log1p([rows[i]["ipl_impact_per_match"] for i in appeared])
    reg = make_pipeline(StandardScaler(), Ridge(alpha=20.0))
    reg.fit(rx, ry, ridge__sample_weight=weights[appeared])
    return clf, reg


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default="work/data")
    ap.add_argument("--domestic-zips", nargs="+", default=DEFAULT_DOMESTIC)
    ap.add_argument("--ipl-zip", default="ipl_csv2.zip")
    ap.add_argument("--people-csv", default="people.csv")
    ap.add_argument("--names-csv", default="names.csv")
    ap.add_argument("--out", default="outputs/hit_rate_benchmark.json")
    args = ap.parse_args()
    data_dir = Path(args.data_dir)
    domestic_b, domestic_w, domestic_dates = {}, {}, {}
    registry, _ = load_name_registry(data_dir / args.people_csv, data_dir / args.names_csv)
    for archive in args.domestic_zips:
        raw = load_deliveries(data_dir / archive)
        comp = Path(archive).name.replace("_csv2.zip", "")
        tagged = [{**row, "season": f"{comp}:{row.get('season', '')}"} for row in raw]
        bat, dates = aggregate(tagged, "bat", registry)
        bowl, _ = aggregate(tagged, "bowl", registry)
        domestic_b.update(bat)
        domestic_w.update(bowl)
        domestic_dates.update(dates)
    ipl_raw = load_deliveries(data_dir / args.ipl_zip)
    ipl_b, ipl_dates = aggregate(ipl_raw, "bat", registry)
    ipl_w, _ = aggregate(ipl_raw, "bowl", registry)
    frame = build_frame(combine(domestic_b, domestic_w), season_bounds(domestic_dates),
                        combine(ipl_b, ipl_w), season_bounds(ipl_dates))
    bounds = season_bounds(domestic_dates)
    sma_seasons = sorted({r["domestic_season"] for r in frame if r["domestic_season"].startswith("sma:")},
                         key=lambda season: bounds[season][1])
    folds = []
    for index, season in enumerate(sma_seasons):
        if index < 4:
            continue
        cutoff = bounds[season][1]
        test = [r for r in frame if r["domestic_season"] == season]
        earlier = [r for r in frame if bounds[r["domestic_season"]][1] < cutoff]
        sma_train = [r for r in earlier if r["domestic_season"].startswith("sma:")]
        if not test or len({r["ipl_next_appearance"] for r in earlier}) < 2 or len({r["ipl_next_appearance"] for r in sma_train}) < 2:
            continue
        all_clf, all_reg = fit_models(earlier)
        sma_clf, sma_reg = fit_models(sma_train)
        decay_models = {}
        for half_life in (2, 4, 8):
            decay_models[half_life] = fit_recency_weighted(earlier, bounds, cutoff, half_life)
        all_p, all_i = predictions(all_clf, all_reg, test)
        sma_p, sma_i = predictions(sma_clf, sma_reg, test)
        labels = [r["ipl_next_appearance"] for r in test]
        all_score = np.asarray(all_p) * np.asarray(all_i)
        sma_score = np.asarray(sma_p) * np.asarray(sma_i)
        blend = .5 * rank_percentile(all_score) + .5 * rank_percentile(sma_score)
        decay_scores = {}
        for half_life, (decay_clf, decay_reg) in decay_models.items():
            dp, di = predictions(decay_clf, decay_reg, test)
            decay_scores[half_life] = np.asarray(dp) * np.asarray(di)
        auc = float(roc_auc_score(labels, all_p)) if len(set(labels)) == 2 else None
        folds.append({
            "validation_season": season,
            "target_ipl_season": test[0]["target_ipl_season"],
            "rows": len(test),
            "appearance_rate": float(np.mean(labels)),
            "roc_auc_multi_league": auc,
            "brier_multi_league": float(brier_score_loss(labels, all_p)),
            "precision_at_10_multi_league_expected_impact": precision_at_10(labels, all_score),
            "precision_at_10_multi_league_appearance_probability": precision_at_10(labels, all_p),
            "precision_at_10_smat_only_expected_impact": precision_at_10(labels, sma_score),
            "precision_at_10_fixed_half_rank_blend": precision_at_10(labels, blend),
            **{f"precision_at_10_recency_half_life_{h}y": precision_at_10(labels, score)
               for h, score in decay_scores.items()},
        })
    metric_names = ["precision_at_10_multi_league_expected_impact",
                    "precision_at_10_multi_league_appearance_probability",
                    "precision_at_10_smat_only_expected_impact",
                    "precision_at_10_fixed_half_rank_blend",
                    "precision_at_10_recency_half_life_2y",
                    "precision_at_10_recency_half_life_4y",
                    "precision_at_10_recency_half_life_8y"]
    means = {name: float(np.mean([f[name] for f in folds])) for name in metric_names}
    result = {"candidate_pool": "SMAT-only seasons; same rows for every comparison",
              "ranking_methods": "chronological fits; no role/age/proprietary fields; no hyperparameter tuning",
              "fold_count": len(folds), "latest_holdout": folds[-1] if folds else None,
              "walk_forward_mean_precision_at_10": means, "folds": folds}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps({"fold_count": len(folds), "latest_holdout": result["latest_holdout"],
                      "walk_forward_mean_precision_at_10": means}, indent=2))


if __name__ == "__main__":
    main()
