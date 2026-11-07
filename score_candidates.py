#!/usr/bin/env python3
"""Create a Round 1 uncapped-player scouting shortlist from a cleaned CSV.

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
    "status": ["uncapped status", "uncapped", "is uncapped", "capped status", "international capped", "capped", "india cap"],
    "season": ["season", "year", "competition season"],
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



def has_status_value(row):
    status_headers = {
        "uncapped status", "uncapped", "is uncapped", "capped status",
        "international capped", "capped", "india cap", "status",
    }
    return any(norm(k) in status_headers and str(v or "").strip() for k, v in row.items())

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


def uncapped_status(row):
    normalized = {norm(k): str(v or "").strip() for k, v in row.items()}
    def classify(value, is_uncapped_field):
        v = norm(value)
        if not v:
            return None
        if is_uncapped_field:
            if v in {"yes", "true", "1", "uncapped", "not capped", "no international caps"}:
                return True
            if v in {"no", "false", "0", "capped", "international"}:
                return False
        else:
            if v in {"no", "false", "0", "uncapped", "not capped", "never capped"}:
                return True
            if v in {"yes", "true", "1", "capped", "international"}:
                return False
        return None
    for key in ("uncapped status", "uncapped", "is uncapped"):
        if normalized.get(norm(key), ""):
            return classify(normalized[norm(key)], True)
    for key in ("capped status", "international capped", "capped", "india cap"):
        if normalized.get(norm(key), ""):
            return classify(normalized[norm(key)], False)
    generic = norm(normalized.get("status", ""))
    if generic in {"uncapped", "not capped", "never capped"}:
        return True
    if generic in {"capped", "international"}:
        return False
    return None


def percentile(values, x):
    a = sorted(v for v in values if math.isfinite(v))
    return 50.0 if not a else 100.0 * (sum(v < x for v in a) + .5) / len(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--secondary-model", help="Optional SMAT-only model; displayed as supplementary historical IPL appearance context only")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-age", type=float, default=None, help="Optional maximum age only if the official challenge rules specify one")
    ap.add_argument("--pack-uncapped", action="store_true",
                    help="Treat missing cap-status fields as uncapped only when every input row comes from the official uncapped-only challenge pack")
    ap.add_argument("--rr-need", choices=["neutral", "powerplay_bowling", "middle_order_bat", "allrounder_cover", "trade_bowler_in"], default="neutral", help="Conditional RR need scenario; neutral by default until retentions are confirmed")
    ap.add_argument("--report", help="Optional path for a coverage and eligibility audit JSON")
    args = ap.parse_args()
    model = joblib.load(args.model)
    secondary_model = joblib.load(args.secondary_model) if args.secondary_model else None
    registry = model.get("name_registry", {})
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        source = list(csv.DictReader(f))
    candidates = []
    audit = {"input_rows": len(source), "missing_name": 0, "missing_age": 0,
             "over_age_limit": 0, "capped_excluded": 0, "missing_batting_and_bowling_volume": 0,
             "uncapped_status_unverified": 0,
             "eligibility_source": "official uncapped-only challenge pack" if args.pack_uncapped else "explicit CSV cap-status field",
             "scored": 0, "max_age": args.max_age, "ranking_method": "60% role-specific skill + 25% relative youth + 15% selected provisional RR need; IPL models are context only"}
    for row in source:
        name = value(row, "name")
        age = age_from(row)
        status = uncapped_status(row)
        if status is None and args.pack_uncapped and not has_status_value(row):
            status = True
        if not name:
            audit["missing_name"] += 1
            continue
        if age is None:
            audit["missing_age"] += 1
            continue
        if age <= 0:
            audit["missing_age"] += 1
            continue
        if args.max_age is not None and age > args.max_age:
            audit["over_age_limit"] += 1
            continue
        if status is None:
            audit["uncapped_status_unverified"] += 1
            continue
        if status is False:
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
                           "role": value(row, "role"), "season": value(row, "season"),
                           "uncapped_status": "uncapped", "matches": int(matches), "runs": int(runs),
                           "strike_rate": round(sr, 2), "average": avg if math.isfinite(avg) else None,
                           "balls": int(balls), "outs": int(outs), "wickets": int(wickets),
                           "bowl_balls": int(bowl_balls), "economy": econ if math.isfinite(econ) else None,
                           "dot_balls": int(dots), "features": feat, "source": row})
    if not candidates:
        raise SystemExit("No eligible rows. Check name, DOB/age, uncapped status and summary stats.")
    audit["scored"] = len(candidates)
    x = np.asarray([[c["features"][f] for f in model["features"]] for c in candidates], dtype=float)
    probs = model["appearance_model"].predict_proba(x)[:, 1]
    impacts = np.maximum(0, np.expm1(model["impact_model"].predict(x)))
    expected = probs * impacts
    if secondary_model:
        smat_probs = secondary_model["appearance_model"].predict_proba(x)[:, 1]
        smat_impacts = np.maximum(0, np.expm1(secondary_model["impact_model"].predict(x)))
    else:
        smat_probs, smat_impacts = probs, impacts
    fit_map = {
        "neutral": {"bat": 50, "bowl": 50, "allround": 50, "keep": 50},
        "powerplay_bowling": {"bat": 40, "bowl": 88, "allround": 68, "keep": 35},
        "middle_order_bat": {"bat": 88, "bowl": 38, "allround": 72, "keep": 60},
        "allrounder_cover": {"bat": 56, "bowl": 56, "allround": 92, "keep": 42},
        "trade_bowler_in": {"bat": 85, "bowl": 35, "allround": 68, "keep": 58},
    }
    def pct(values, value, higher=True):
        if value is None or not math.isfinite(value):
            return None
        result = percentile(values, value)
        return result if higher else 100.0 - result
    def weighted(parts):
        usable = [(v, w) for v, w in parts if v is not None and math.isfinite(v)]
        return sum(v*w for v, w in usable) / sum(w for _, w in usable) if usable else 50.0
    def role_group(c):
        r = norm(c["role"])
        return "allround" if c["features"]["allrounder"] else "bowl" if c["features"]["bowler"] else "keep" if "keeper" in r else "bat"
    bat_pool = [c for c in candidates if role_group(c) in {"bat", "keep", "allround"} and c["balls"] > 0]
    bowl_pool = [c for c in candidates if role_group(c) in {"bowl", "allround"} and (c["bowl_balls"] > 0 or c["wickets"] > 0)]
    for c, p, impact, exp, sp, si in zip(candidates, probs, impacts, expected, smat_probs, smat_impacts):
        role = role_group(c)
        sr_pct = pct([v["strike_rate"] for v in bat_pool], c["strike_rate"] if c["balls"] else None)
        avg_pct = pct([v["average"] for v in bat_pool if v["average"] is not None], c["average"])
        rpm = c["runs"] / c["matches"] if c["matches"] else None
        rpm_pct = pct([v["runs"] / v["matches"] for v in bat_pool if v["matches"]], rpm)
        bat_depth = min(100.0, 100.0 * c["balls"] / 240.0) if c["balls"] else None
        bat_score = weighted([(sr_pct, .35), (avg_pct, .25), (rpm_pct, .20), (bat_depth, .20)])
        wicket_rate = c["wickets"] * 24.0 / c["bowl_balls"] if c["bowl_balls"] else None
        wicket_pct = pct([v["wickets"] * 24.0 / v["bowl_balls"] for v in bowl_pool if v["bowl_balls"]], wicket_rate)
        econ_pct = pct([v["economy"] for v in bowl_pool if v["economy"] is not None], c["economy"], False)
        dot_rate = c["dot_balls"] / c["bowl_balls"] if c["bowl_balls"] else None
        dot_pct = pct([v["dot_balls"] / v["bowl_balls"] for v in bowl_pool if v["bowl_balls"]], dot_rate)
        bowl_depth = min(100.0, 100.0*c["bowl_balls"]/180.0) if c["bowl_balls"] else None
        bowl_score = weighted([(wicket_pct, .35), (econ_pct, .25), (dot_pct, .20), (bowl_depth, .20)])
        has_bat, has_bowl = c["balls"] > 0, c["bowl_balls"] > 0 or c["wickets"] > 0
        talent = bowl_score if role == "bowl" else bat_score if role in {"bat", "keep"} else (weighted([(bat_score, .5), (bowl_score, .5)]) if has_bat and has_bowl else weighted([(bat_score if has_bat else bowl_score, .7), (50, .3)]))
        age_score = 100.0 - percentile([v["age"] for v in candidates], c["age"])
        role_fit = fit_map[args.rr_need][role]
        score = .60*talent + .25*age_score + .15*role_fit
        strengths = []
        if c["balls"]:
            strengths.append(f"bat SR {c['strike_rate']:.1f} over {c['balls']} balls")
        if c["outs"] and c["average"] is not None:
            strengths.append(f"average {c['average']:.1f}")
        if c["wickets"]:
            strengths.append(f"{c['wickets']} wickets from {c['bowl_balls']} balls")
        if c["bowl_balls"] and c["economy"] is not None:
            strengths.append(f"economy {c['economy']:.2f}")
        if not strengths:
            strengths.append(f"{c['matches']} matches; performance evidence incomplete")
        risks = []
        if c["matches"] < 10: risks.append(f"small sample ({c['matches']} matches)")
        if role in {"bat", "keep", "allround"} and c["balls"] < 100: risks.append("limited batting sample")
        if role in {"bowl", "allround"} and c["bowl_balls"] < 60: risks.append("limited bowling sample")
        if role == "allround" and not (has_bat and has_bowl): risks.append("two-skill role needs verification")
        if not risks: risks.append("verify role, availability and original scorecards")
        c.update({"role_group": role, "skill_score": round(talent, 1), "youth_score": round(age_score, 1),
                  "rr_fit_score": role_fit, "rr_need_scenario": args.rr_need, "scouting_score": round(score, 1),
                  "why_consider": f"Age {c['age']:.1f}; {role}; " + "; ".join(strengths),
                  "risk_checks": "; ".join(risks), "ipl_appearance_signal": float(p),
                  "ipl_impact_per_match": float(impact), "expected_ipl_impact": float(exp),
                  "smat_appearance_signal": float(sp), "smat_impact_per_match": float(si),
                  "smat_expected_impact": float(sp*si), "uncapped_status": "uncapped"})
    ranked = sorted(candidates, key=lambda c: (-c["scouting_score"], c["age"], -c["matches"]))
    fields = ["rank", "player", "age", "team", "role", "season", "uncapped_status", "role_group", "rr_need_scenario",
              "skill_score", "youth_score", "rr_fit_score", "scouting_score", "why_consider", "risk_checks",
              "matches", "runs", "balls", "average", "strike_rate", "wickets", "bowl_balls", "economy", "dot_balls",
              "ipl_appearance_signal", "ipl_impact_per_match", "expected_ipl_impact", "smat_appearance_signal", "smat_expected_impact"]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, c in enumerate(ranked, 1):
            w.writerow({"rank": i, **{k: c.get(k, "") for k in fields if k != "rank"}})
    if args.report:
        import json
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2)
    print(f"Scored {len(candidates)} eligible uncapped candidates using the scouting rubric (no age limit applied); wrote {args.output}")


if __name__ == "__main__":
    main()
