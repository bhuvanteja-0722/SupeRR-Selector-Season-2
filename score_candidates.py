#!/usr/bin/env python3
"""Score a cleaned player-summary CSV with the trained RR Scout baseline.

Example:
  python3 score_candidates.py --model rr_scout_model.joblib --input candidates.csv --output ranked.csv

Use one season/competition summary per player and verify identities first. The
private challenge pack should remain local; this script writes only to the path
you specify and does not upload or transmit any file.
"""
import argparse
import csv
import math
import re
from datetime import date, datetime

import joblib
import numpy as np


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split())


ALIASES = {
    "name": ["player", "player name", "name", "full name", "cricketer"],
    "age": ["age", "age years", "age_years"], "dob": ["dob", "date of birth", "birth date"],
    "birth_year": ["year of birth", "birth year", "yob"],
    "team": ["team", "state", "association", "side"], "role": ["role", "player role", "specialism", "specialty"],
    "status": ["uncapped status", "capped status", "international capped", "capped", "india cap"],
    "matches": ["matches", "mat", "m"], "innings": ["batting innings", "innings batted", "innings", "inns", "inn"],
    "runs": ["runs", "r"], "balls": ["balls faced", "balls_faced", "bf"],
    "outs": ["dismissals", "outs", "wickets lost", "out"], "sr": ["strike rate", "strike_rate", "sr"],
    "average": ["average", "batting average", "avg"], "wickets": ["wickets", "wkts", "wkt"],
    "bowl_balls": ["balls bowled", "balls_bowled", "bowling balls"],
    "conceded": ["runs conceded", "runs_conceded", "bowling runs", "runs against"],
    "economy": ["economy", "econ", "economy rate"], "dots": ["dot balls", "dots", "dot balls bowled"]
}


def value(row, name):
    normalized = {norm(k): v for k, v in row.items()}
    for h in ALIASES[name]:
        if normalized.get(norm(h), "") != "":
            return normalized[norm(h)]
    return ""


def number(v, default=0.0):
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return default


def age_from(row):
    age = number(value(row, "age"), -1)
    if age >= 0:
        return age
    birth_year = number(value(row, "birth_year"), -1)
    if birth_year > 1900:
        return 2026 - birth_year
    raw = value(row, "dob")
    if not raw:
        return None
    parsed = None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d-%b-%Y", "%d %B %Y"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            break
        except ValueError:
            continue
    return ((date(2026, 11, 8) - parsed).days / 365.2425) if parsed else None


def percentile(values, x):
    a = sorted(v for v in values if math.isfinite(v))
    return 50.0 if not a else 100.0 * (sum(v < x for v in a) + .5) / len(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-age", type=float, default=25)
    ap.add_argument("--report", help="Optional path for a coverage and eligibility audit JSON")
    args = ap.parse_args()
    model = joblib.load(args.model)
    registry = model.get("name_registry", {})
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        source = list(csv.DictReader(f))
    candidates = []
    audit = {"input_rows": len(source), "missing_name": 0, "missing_age": 0,
             "over_age_limit": 0, "capped_excluded": 0, "missing_batting_and_bowling_volume": 0,
             "scored": 0, "max_age": args.max_age}
    for row in source:
        name = value(row, "name")
        age = age_from(row)
        status = norm(value(row, "status"))
        if not name:
            audit["missing_name"] += 1
            continue
        if age is None:
            audit["missing_age"] += 1
            continue
        if age > args.max_age:
            audit["over_age_limit"] += 1
            continue
        if re.search(r"(^| )(yes|true|capped)( |$)", status) and "uncapped" not in status and "not capped" not in status:
            audit["capped_excluded"] += 1
            continue
        matches = number(value(row, "matches"))
        runs, balls, outs = number(value(row, "runs")), number(value(row, "balls")), number(value(row, "outs"))
        wickets, bowl_balls = number(value(row, "wickets")), number(value(row, "bowl_balls"))
        conceded, dots = number(value(row, "conceded")), number(value(row, "dots"))
        if matches <= 0 and balls <= 0 and bowl_balls <= 0:
            audit["missing_batting_and_bowling_volume"] += 1
            continue
        raw_sr, raw_avg, raw_econ = value(row, "sr"), value(row, "average"), value(row, "economy")
        sr = number(raw_sr, 100 * runs / balls if balls else 0)
        avg = number(raw_avg, runs / outs if outs else runs)
        econ = number(raw_econ, 6 * conceded / bowl_balls if bowl_balls else 0)
        role = norm(value(row, "role"))
        is_bat = any(k in role for k in ("bat", "opener", "middle"))
        is_bowl = any(k in role for k in ("bowl", "pace", "spin", "fast"))
        allround = "all round" in role or "allround" in role or (runs >= 100 and wickets >= 3)
        if not is_bat and not is_bowl and not allround:
            is_bowl = wickets >= 3 and runs < 100
        innings = number(value(row, "innings"))
        feat = {"log_matches": math.log1p(matches), "log_innings": math.log1p(innings),
                "log_runs": math.log1p(runs), "log_balls": math.log1p(balls), "sr": sr,
                "bat_average": avg, "log_wickets": math.log1p(wickets),
                "wickets_per_over": wickets * 6 / bowl_balls if bowl_balls else 0,
                "econ": econ, "dot_rate": dots / bowl_balls if bowl_balls else 0,
                "allrounder": int(allround), "bowler": int(is_bowl and not allround)}
        candidates.append({"player": name, "age": age, "team": value(row, "team"),
                           "role": value(row, "role"), "matches": int(matches), "runs": int(runs),
                           "strike_rate": round(sr, 2), "wickets": int(wickets),
                           "features": feat, "source": row})
    if not candidates:
        raise SystemExit("No eligible rows. Check name, DOB/age, uncapped status and summary stats.")
    audit["scored"] = len(candidates)
    x = np.asarray([[c["features"][f] for f in model["features"]] for c in candidates], dtype=float)
    probs = model["appearance_model"].predict_proba(x)[:, 1]
    impacts = np.maximum(0, np.expm1(model["impact_model"].predict(x)))
    roles = []
    for c in candidates:
        r = norm(c["role"])
        roles.append("allround" if "all round" in r or "allround" in r or c["features"]["allrounder"] else
                     "bowl" if c["features"]["bowler"] else "keep" if "keeper" in r else "bat")
    fit = {"bat": 78, "bowl": 78, "allround": 88, "keep": 64}
    expected = [float(p * i) for p, i in zip(probs, impacts)]
    for c, p, impact, exp, role in zip(candidates, probs, impacts, expected, roles):
        c.update({"ipl_appearance_probability": float(p), "ipl_impact_per_match": float(impact),
                  "expected_ipl_impact": float(exp), "role_group": role,
                  "rr_fit_score": fit[role]})
    for c in candidates:
        c["score_100"] = (.70 * percentile(expected, c["expected_ipl_impact"]) +
                           .20 * percentile([26 - p["age"] for p in candidates], 26 - c["age"]) +
                           .10 * c["rr_fit_score"])
    ranked = sorted(candidates, key=lambda c: c["score_100"], reverse=True)
    fields = ["rank", "player", "age", "team", "role", "matches", "runs", "strike_rate", "wickets",
              "ipl_appearance_probability", "ipl_impact_per_match", "expected_ipl_impact", "rr_fit_score", "score_100"]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, c in enumerate(ranked, 1):
            w.writerow({"rank": i, **{k: c.get(k, "") for k in fields if k != "rank"}})
    if args.report:
        import json
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2)
    print(f"Scored {len(candidates)} age-qualified uncapped candidates; wrote {args.output}")


if __name__ == "__main__":
    main()
