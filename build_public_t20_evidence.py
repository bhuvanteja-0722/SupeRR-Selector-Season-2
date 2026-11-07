#!/usr/bin/env python3
"""Build a recent public T20 evidence bundle to enrich challenge-pack players.

The bundle contains only the latest available season per player and competition
from the repository's 18 Cricsheet domestic/franchise T20 archives. It has no
age or uncapped labels; eligibility must come from the challenge pack or a
separately verified profile.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

from train_model import aggregate, combine, load_deliveries, load_name_registry, norm, season_bounds

ARCHIVES = [
    "sma_csv2.zip", "bbl_csv2.zip", "bpl_csv2.zip", "cpl_csv2.zip",
    "ctc_csv2.zip", "etpl_male_csv2.zip", "ilt_csv2.zip", "ipt_male_csv2.zip",
    "lpl_csv2.zip", "mct_male_csv2.zip", "mlc_csv2.zip", "msl_male_csv2.zip",
    "npl_male_csv2.zip", "ntb_male_csv2.zip", "pro20_male_csv2.zip",
    "psl_csv2.zip", "sat_csv2.zip", "ssm_male_csv2.zip",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="work/data")
    parser.add_argument("--out", default="outputs/public_t20_evidence.csv")
    args = parser.parse_args()
    data = Path(args.data_dir)
    registry, display = load_name_registry(data / "people.csv", data / "names.csv")
    display_by_norm_id = {norm(ident): name for ident, name in display.items()}
    aliases_by_id = defaultdict(set)
    for alias, ident in registry.items():
        aliases_by_id[norm(ident)].add(alias)
    rows = []
    for archive in ARCHIVES:
        path = data / archive
        comp = Path(archive).name.replace("_csv2.zip", "")
        raw = load_deliveries(path)
        tagged = [{**r, "season": f"{comp}:{r.get('season', '')}"} for r in raw]
        bat, dates = aggregate(tagged, "bat", registry)
        bowl, _ = aggregate(tagged, "bowl", registry)
        seasons = season_bounds(dates)
        stats = combine(bat, bowl)
        latest = {}
        for (season, player), summary in stats.items():
            if not season.startswith(comp + ":") or season not in seasons:
                continue
            if player not in latest or seasons[season][1] > seasons[latest[player]][1]:
                latest[player] = season
        for (season, player), s in stats.items():
            if latest.get(player) != season:
                continue
            ident = player if player in display_by_norm_id else ""
            name = display_by_norm_id.get(player, player)
            balls, runs, outs = s.get("bat_balls", 0), s.get("runs", 0), s.get("outs", 0)
            bowl_balls, wickets = s.get("bowl_balls", 0), s.get("wickets", 0)
            role = "all-rounder" if runs >= 100 and wickets >= 3 else (
                "bowler" if wickets >= 3 or bowl_balls > 0 else "batter")
            rows.append({
                "player": name,
                "player_id": ident,
                "aliases": " | ".join(sorted(aliases_by_id.get(player, set()))),
                "identity_confidence": "Cricsheet register" if ident else "name only; verify identity",
                "competition": comp,
                "season": season.split(":", 1)[1],
                "role": role,
                "matches": int(s.get("matches", 0)),
                "innings": int(s.get("innings", 0)),
                "runs": int(runs),
                "balls faced": int(balls),
                "dismissals": int(outs),
                "strike rate": round(100 * runs / balls, 3) if balls else 0,
                "average": round(runs / outs, 3) if outs else runs,
                "wickets": int(wickets),
                "balls bowled": int(bowl_balls),
                "runs conceded": int(s.get("runs_conceded", 0)),
                "economy": round(6 * s.get("runs_conceded", 0) / bowl_balls, 3) if bowl_balls else 0,
                "dot balls": int(s.get("dots", 0)),
            })
    rows.sort(key=lambda r: (r["player"].casefold(), r["season"], r["competition"]))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} latest player-competition-season evidence rows from {len(ARCHIVES)} public archives to {out}")


if __name__ == "__main__":
    main()
