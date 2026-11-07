#!/usr/bin/env python3
"""Train a time-split multi-league T20 to next-IPL contribution baseline.

Inputs are Cricsheet Ashwin CSV ZIP archives. This model predicts (1) next-IPL
appearance and (2) per-match impact conditional on appearing. Expected impact is
their product. It is a research baseline; it does not use age or private fields.

Example:
  python3 train_model.py --domestic-zips sma_csv2.zip bbl_csv2.zip --ipl-zip ipl_csv2.zip --out model_artifacts
"""
import argparse
import csv
import json
import joblib
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, mean_absolute_error, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


FEATURES = ["log_matches", "log_innings", "log_runs", "log_balls", "sr",
            "bat_average", "log_wickets", "wickets_per_over", "econ", "dot_rate",
            "allrounder", "bowler"]


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split())


def as_int(s):
    try:
        return int(float(s or 0))
    except (ValueError, TypeError):
        return 0


def load_deliveries(path):
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if Path(n).name.lower() == "all_matches.csv"), None)
        if name is None:
            raise ValueError(f"{path}: no all_matches.csv inside archive")
        with z.open(name) as f:
            return list(csv.DictReader(line.decode("utf-8-sig") for line in f))


def load_name_registry(people_path=None, names_path=None):
    variants = defaultdict(set)
    display = {}
    if people_path:
        with open(people_path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                ident = (r.get("identifier") or "").strip()
                if not ident:
                    continue
                display[ident] = r.get("name", "") or r.get("unique_name", "")
                for col in ("name", "unique_name"):
                    if r.get(col):
                        variants[norm(r[col])].add(ident)
    if names_path:
        with open(names_path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                ident, name = (r.get("identifier") or "").strip(), r.get("name", "")
                if ident and name:
                    variants[norm(name)].add(ident)
    # Ambiguous names are intentionally not auto-merged.
    return {name: next(iter(ids)) for name, ids in variants.items() if len(ids) == 1}, display


def aggregate(deliveries, side, name_registry=None):
    stats = defaultdict(lambda: defaultdict(float))
    dates = defaultdict(list)
    matches = defaultdict(set)
    innings = defaultdict(set)
    batter_innings_seen = set()
    for r in deliveries:
        player_field = "striker" if side == "bat" else "bowler"
        player_name = r.get(player_field, "").strip()
        if not player_name:
            continue
        player = (name_registry or {}).get(norm(player_name), norm(player_name))
        season = r.get("season", "")
        k = (season, norm(player))
        match = r.get("match_id", "")
        inn = r.get("innings", "")
        dates[season].append(r.get("start_date", ""))
        if match:
            matches[k].add(match)
        if inn and match:
            innings[k].add((match, inn))
        s = stats[k]
        runs = as_int(r.get("runs_off_bat"))
        wides, noballs = as_int(r.get("wides")), as_int(r.get("noballs"))
        if side == "bat":
            s["runs"] += runs
            s["balls"] += int(wides == 0)
            batter_innings_key = (match, inn, player)
            if match and inn and batter_innings_key not in batter_innings_seen:
                s["bat_innings"] += 1
                batter_innings_seen.add(batter_innings_key)
            dismissed_raw = norm(r.get("player_dismissed", ""))
            dismissed = (name_registry or {}).get(dismissed_raw, dismissed_raw)
            wicket = norm(r.get("wicket_type", ""))
            if dismissed == player and wicket not in {"run out", "retired hurt", "retired out", "obstructing the field"}:
                s["outs"] += 1
        else:
            s["runs_conceded"] += runs + wides + noballs
            legal = int(wides == 0 and noballs == 0)
            s["balls"] += legal
            extras = as_int(r.get("extras"))
            s["dots"] += int(legal and runs + extras == 0)
            dismissed = r.get("player_dismissed", "").strip()
            wicket = norm(r.get("wicket_type", ""))
            if dismissed and wicket not in {"run out", "retired hurt", "retired out", "obstructing the field"}:
                s["wickets"] += 1
    result = {}
    for (season, player), s in stats.items():
        runs, balls, outs = s["runs"], s["balls"], s["outs"]
        wickets, bowl_balls = s["wickets"], s["balls"]
        sr = 100 * runs / balls if side == "bat" and balls else 0
        avg = runs / outs if side == "bat" and outs else runs if side == "bat" else 0
        econ = 6 * s["runs_conceded"] / bowl_balls if side == "bowl" and bowl_balls else 0
        result[(season, player)] = {"runs": runs if side == "bat" else 0,
                                    "bat_balls": balls if side == "bat" else 0,
                                    "outs": outs, "sr": sr, "avg": avg,
                                    "wickets": wickets if side == "bowl" else 0,
                                    "bowl_balls": bowl_balls if side == "bowl" else 0,
                                    "runs_conceded": s["runs_conceded"], "econ": econ,
                                    "dots": s["dots"], "matches": len(matches[(season, player)]),
                                    "innings": int(s.get("bat_innings", 0)) if side == "bat" else len(innings[(season, player)])}
    return result, dates


def combine(bat, bowl):
    result = {}
    for k in set(bat) | set(bowl):
        b, w = bat.get(k, {}), bowl.get(k, {})
        balls, runs, outs = b.get("bat_balls", 0), b.get("runs", 0), b.get("outs", 0)
        bb, wickets = w.get("bowl_balls", 0), w.get("wickets", 0)
        item = {**b, **w}
        item.update({"runs": runs, "bat_balls": balls, "outs": outs,
                     "sr": 100 * runs / balls if balls else 0,
                     "bat_average": runs / outs if outs else runs,
                     "wickets": wickets, "bowl_balls": bb,
                     "wickets_per_over": wickets * 6 / bb if bb else 0,
                     "dot_rate": w.get("dots", 0) / bb if bb else 0,
                     "matches": max(b.get("matches", 0), w.get("matches", 0)),
                     "innings": b.get("innings", 0)})
        item["allrounder"] = int(runs >= 100 and wickets >= 3)
        item["bowler"] = int(wickets >= 3 and runs < 100)
        item["log_matches"] = math.log1p(item["matches"])
        item["log_innings"] = math.log1p(item["innings"])
        item["log_runs"] = math.log1p(runs)
        item["log_balls"] = math.log1p(balls)
        item["log_wickets"] = math.log1p(wickets)
        result[k] = item
    return result


def season_bounds(dates):
    return {season: (min(filter(None, values)), max(filter(None, values)))
            for season, values in dates.items() if any(values)}


def build_frame(domestic, domestic_bounds, ipl, ipl_bounds):
    rows = []
    ipl_starts = {season: bounds[0] for season, bounds in ipl_bounds.items()}
    for season, bounds in domestic_bounds.items():
        cutoff = bounds[1]
        later = [(start, key) for key, start in ipl_starts.items() if start > cutoff]
        if not later:
            continue
        target_season = min(later)[1]
        candidates = [(k, v) for k, v in domestic.items() if k[0] == season]
        for (_, player), feats in candidates:
            outcome = ipl.get((target_season, player), {})
            played = int(outcome.get("matches", 0) > 0)
            impact = ((outcome.get("runs", 0) + 20 * outcome.get("wickets", 0)) /
                      outcome.get("matches", 1)) if played else 0.0
            rows.append({"player": player, "domestic_season": season,
                         "target_ipl_season": target_season, **feats,
                         "ipl_next_appearance": played,
                         "ipl_impact_per_match": impact})
    return rows


def fit_models(train_rows):
    x = np.asarray([[r[f] for f in FEATURES] for r in train_rows], dtype=float)
    y = np.asarray([r["ipl_next_appearance"] for r in train_rows], dtype=int)
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=.35, max_iter=2000))
    clf.fit(x, y)
    appeared = [r for r in train_rows if r["ipl_next_appearance"]]
    rx = np.asarray([[r[f] for f in FEATURES] for r in appeared], dtype=float)
    ry = np.log1p([r["ipl_impact_per_match"] for r in appeared])
    reg = make_pipeline(StandardScaler(), Ridge(alpha=20.0))
    reg.fit(rx, ry)
    return clf, reg


def predictions(clf, reg, rows):
    if not rows:
        return [], []
    x = np.asarray([[r[f] for f in FEATURES] for r in rows], dtype=float)
    probability = clf.predict_proba(x)[:, 1]
    impact = np.maximum(0, np.expm1(reg.predict(x)))
    return probability.tolist(), impact.tolist()


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sma-zip", help="Legacy single-SMAT input")
    ap.add_argument("--domestic-zips", nargs="+", help="Domestic/franchise T20 archives to combine")
    ap.add_argument("--ipl-zip", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--people-csv")
    ap.add_argument("--names-csv")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    domestic_paths = args.domestic_zips or ([args.sma_zip] if args.sma_zip else [])
    if not domestic_paths:
        ap.error("provide --domestic-zips (or legacy --sma-zip)")
    domestic_raw = [load_deliveries(p) for p in domestic_paths]
    ipl_raw = load_deliveries(args.ipl_zip)
    registry, display_names = load_name_registry(args.people_csv, args.names_csv)
    ipl_b, ipl_dates = aggregate(ipl_raw, "bat", registry)
    ipl_w, _ = aggregate(ipl_raw, "bowl", registry)
    # Combine batting and bowling by player-season across sources. The shared
    # Cricsheet ID handles most variants; unresolvable aliases remain separate.
    domestic_b, domestic_w, domestic_dates = {}, {}, {}
    for path, raw in zip(domestic_paths, domestic_raw):
        comp = Path(path).name.replace("_csv2.zip", "")
        # Competition prefix avoids merging overlapping seasons from separate
        # leagues while retaining chronology for forward validation.
        tagged = [{**r, "season": f"{comp}:{r.get('season','')}"} for r in raw]
        bat, dates = aggregate(tagged, "bat", registry)
        bowl, _ = aggregate(tagged, "bowl", registry)
        domestic_b.update(bat)
        domestic_w.update(bowl)
        domestic_dates.update(dates)
    domestic, future_ipl = combine(domestic_b, domestic_w), combine(ipl_b, ipl_w)
    domestic_bounds, ipl_bounds = season_bounds(domestic_dates), season_bounds(ipl_dates)
    frame = build_frame(domestic, domestic_bounds, future_ipl, ipl_bounds)
    seasons = sorted({r["domestic_season"] for r in frame}, key=lambda s: domestic_bounds.get(s, ("", ""))[1])
    if len(seasons) < 3:
        raise SystemExit(f"Only {len(seasons)} domestic seasons have a later IPL label; need at least 3.")
    holdout = seasons[-1]
    train = [r for r in frame if domestic_bounds[r["domestic_season"]][1] < domestic_bounds[holdout][1]]
    test = [r for r in frame if r["domestic_season"] == holdout]
    if len({r["ipl_next_appearance"] for r in train}) < 2:
        raise SystemExit("Training period lacks both appearance classes; expand the training window.")
    clf, reg = fit_models(train)
    p, impact = predictions(clf, reg, test)
    for r, prob, pred in zip(test, p, impact):
        r["player_name"] = display_names.get(r["player"], r["player"])
        r["predicted_ipl_appearance_probability"] = prob
        r["predicted_ipl_impact_per_match"] = pred
        r["predicted_expected_impact"] = prob * pred
    scored = sorted(test, key=lambda r: r["predicted_expected_impact"], reverse=True)
    top_n = min(10, len(test))
    hit_at_10 = sum(r["ipl_next_appearance"] for r in scored[:top_n]) / max(1, top_n)
    prob_ranked_test = sorted(zip(test, p), key=lambda x: x[1], reverse=True)
    probability_hit_at_10 = float(np.mean([r["ipl_next_appearance"] for r, _ in prob_ranked_test[:top_n]]))
    labels = [r["ipl_next_appearance"] for r in test]
    threshold_labels = [int(v >= .5) for v in p]
    holdout_prevalence = float(np.mean(labels))
    walk_forward = []
    for idx, validation_season in enumerate(seasons):
        if idx < 4:
            continue
        prior_seasons = set(seasons[:idx])
        fold_train = [r for r in frame if r["domestic_season"] in prior_seasons]
        fold_test = [r for r in frame if r["domestic_season"] == validation_season]
        if len({r["ipl_next_appearance"] for r in fold_train}) < 2 or not fold_test:
            continue
        fold_clf, fold_reg = fit_models(fold_train)
        fp, fi = predictions(fold_clf, fold_reg, fold_test)
        fy = [r["ipl_next_appearance"] for r in fold_test]
        fold_top_n = min(10, len(fold_test))
        expected_top = sorted(zip(fold_test, fp, fi), key=lambda z: z[1] * z[2], reverse=True)[:fold_top_n]
        probability_top = sorted(zip(fold_test, fp), key=lambda z: z[1], reverse=True)[:fold_top_n]
        walk_forward.append({"validation_season": validation_season,
                             "target_ipl_season": fold_test[0]["target_ipl_season"],
                             "rows": len(fold_test),
                             "roc_auc": float(roc_auc_score(fy, fp)) if len(set(fy)) == 2 else None,
                             "brier_score": float(brier_score_loss(fy, fp)),
                             "precision_at_10_appearance": float(np.mean([x[0]["ipl_next_appearance"] for x in expected_top])),
                             "precision_at_10_by_appearance_probability": float(np.mean([x[0]["ipl_next_appearance"] for x in probability_top]))})
    metrics = {"training_rows": len(train), "training_seasons": seasons[:-1],
               "holdout_season": holdout, "holdout_target_ipl_season": test[0]["target_ipl_season"],
               "holdout_rows": len(test), "holdout_appearance_rate": holdout_prevalence,
               "precision_at_10_for_appearance": hit_at_10,
               "precision_at_10_by_appearance_probability": probability_hit_at_10,
               "accuracy_at_probability_0_5": float(np.mean(np.asarray(labels) == np.asarray(threshold_labels))),
               "naive_all_no_accuracy": 1.0 - holdout_prevalence,
               "brier_score": float(brier_score_loss(labels, p)),
               "naive_prevalence_brier_score": holdout_prevalence * (1 - holdout_prevalence),
               "roc_auc": float(roc_auc_score(labels, p)) if len(set(labels)) == 2 else None,
               "regression_mae_on_appearances": float(mean_absolute_error(
                   [r["ipl_impact_per_match"] for r in test if r["ipl_next_appearance"]],
                   [pred for r, pred in zip(test, impact) if r["ipl_next_appearance"]])) if any(labels) else None,
               "feature_list": FEATURES,
               "label_definition": "next later IPL season appearance; impact=(IPL runs + 20*wickets)/matches",
               "training_archives": [str(Path(p).name) for p in domestic_paths],
               "label_archives": [str(Path(args.ipl_zip).name)],
               "name_matching": ("Cricsheet people/name register; ambiguous variants are not auto-merged"
                                 if registry else "exact normalized text only; unresolved aliases are treated as non-appearances"),
               "walk_forward_folds": walk_forward,
               "walk_forward_mean_precision_at_10": float(np.mean([f["precision_at_10_appearance"] for f in walk_forward])) if walk_forward else None,
               "walk_forward_mean_precision_at_10_by_appearance_probability": float(np.mean([f["precision_at_10_by_appearance_probability"] for f in walk_forward])) if walk_forward else None,
               "smat_walk_forward_folds": [f for f in walk_forward if f["validation_season"].startswith("sma:")],
               "smat_walk_forward_mean_precision_at_10_expected_impact": float(np.mean([f["precision_at_10_appearance"] for f in walk_forward if f["validation_season"].startswith("sma:")])) if any(f["validation_season"].startswith("sma:") for f in walk_forward) else None,
               "smat_walk_forward_mean_precision_at_10_appearance_probability": float(np.mean([f["precision_at_10_by_appearance_probability"] for f in walk_forward if f["validation_season"].startswith("sma:")])) if any(f["validation_season"].startswith("sma:") for f in walk_forward) else None,
               "walk_forward_mean_auc": float(np.mean([f["roc_auc"] for f in walk_forward if f["roc_auc"] is not None])) if any(f["roc_auc"] is not None for f in walk_forward) else None}
    (out / "holdout_metrics.json").write_text(json.dumps(metrics, indent=2))
    columns = ["player_name", "domestic_season", "target_ipl_season", "matches", "innings", "runs",
               "bat_balls", "outs", "sr", "bat_average", "wickets", "bowl_balls", "econ",
               "ipl_next_appearance", "ipl_impact_per_match", "predicted_ipl_appearance_probability",
               "predicted_ipl_impact_per_match", "predicted_expected_impact"]
    write_csv(out / "latest_season_holdout.csv", scored, columns)
    # Fit deployable version on every historically labeled domestic/franchise season.
    full_clf, full_reg = fit_models(frame)
    joblib.dump({"appearance_model": full_clf, "impact_model": full_reg,
                 "features": FEATURES, "training_seasons": seasons,
                 "label_definition": metrics["label_definition"],
                 "identity_source": "Cricsheet people.csv + names.csv; ODC-BY attributed",
                 "score_definition": "appearance probability x predicted per-match impact"},
                out / "rr_scout_model.joblib")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
