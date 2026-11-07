#!/usr/bin/env python3
"""Aggregate Cricsheet Ashwin CSV deliveries into one player summary CSV.

Usage:
  python3 prepare_cricsheet.py deliveries.csv player_master.csv > player_summary.csv

player_master.csv should include player,age (or dob),team,role,uncapped status.
This script only aggregates; verify names and player identity before using results.
"""
import csv
import sys
from collections import defaultdict
from datetime import date


def key(s):
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in (s or "")).split())


def field(row, *names):
    normalized = {key(k): v for k, v in row.items()}
    for name in names:
        value = normalized.get(key(name), "")
        if value != "":
            return value
    return ""


def integer(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    delivery_path = sys.argv[1]
    master_path = sys.argv[2] if len(sys.argv) > 2 else None
    stats = defaultdict(lambda: defaultdict(int))
    match_names = defaultdict(set)
    with open(delivery_path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            match = field(r, "match_id", "match")
            inn = field(r, "innings", "inning")
            season = field(r, "season", "year")
            bat = field(r, "striker", "batter")
            bowl = field(r, "bowler")
            runs = integer(field(r, "runs_off_bat", "batter runs", "batter runs scored"))
            wides = integer(field(r, "wides", "wide"))
            noballs = integer(field(r, "noballs", "no balls", "noball"))
            byes = integer(field(r, "byes"))
            legbyes = integer(field(r, "legbyes", "leg byes"))
            extras = integer(field(r, "extras"))
            if extras == 0:
                extras = wides + noballs + byes + legbyes
            dismissed = field(r, "player_dismissed", "player dismissed")
            wicket = field(r, "wicket_type", "wicket type")
            if bat:
                s = stats[(season, bat)]
                s["runs"] += runs
                s["balls_faced"] += int(wides == 0)
                if match:
                    match_names[(season, match, bat)].add(inn)
                s["outs"] += int(bool(dismissed) and dismissed == bat and key(wicket) not in {"run out", "retired hurt", "obstructing the field", "retired out"})
            if bowl:
                s = stats[(season, bowl)]
                s["runs_conceded"] += runs + wides + noballs
                s["balls_bowled"] += int(wides == 0 and noballs == 0)
                s["dot_balls"] += int(wides == 0 and noballs == 0 and runs + extras == 0)
                s["wickets"] += int(bool(dismissed) and key(wicket) not in {"run out", "retired hurt", "obstructing the field", "retired out"})
                if match:
                    match_names[(season, match, bowl)].add(inn)
            # Count fielding events from available fielder columns.
            if wicket and key(wicket) in {"caught", "stumped", "run out"}:
                fld = field(r, "fielder_1", "fielder")
                if fld:
                    stat = "stumpings" if key(wicket) == "stumped" else "catches" if key(wicket) == "caught" else "run_outs"
                    stats[(season, fld)][stat] += 1

    meta = {}
    if master_path:
        with open(master_path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                name = field(r, "player", "player name", "name")
                if name:
                    meta[key(name)] = r
    header = ["player", "season", "age", "dob", "team", "role", "uncapped status", "matches", "innings", "runs", "balls faced", "dismissals", "strike rate", "average", "wickets", "balls bowled", "runs conceded", "economy", "dot balls", "catches", "stumpings", "run outs"]
    out = csv.writer(sys.stdout)
    out.writerow(header)
    for (season, name), s in sorted(stats.items(), key=lambda item: (item[0][0], item[0][1].casefold())):
        m = meta.get(key(name), {})
        matches = len({match for (yr, match, player) in match_names if yr == season and player == name})
        innings = len({(match, inn) for (yr, match, player), inns in match_names.items()
                       if yr == season and player == name for inn in inns if inn})
        bf, outs, bb = s["balls_faced"], s["outs"], s["balls_bowled"]
        sr = 100 * s["runs"] / bf if bf else ""
        avg = s["runs"] / outs if outs else ""
        econ = 6 * s["runs_conceded"] / bb if bb else ""
        out.writerow([name, season, field(m, "age"), field(m, "dob", "date of birth"), field(m, "team", "state"), field(m, "role", "specialism"), field(m, "uncapped status", "capped"), matches, innings, s["runs"], bf, outs, round(sr, 2) if sr != "" else "", round(avg, 2) if avg != "" else "", s["wickets"], bb, s["runs_conceded"], round(econ, 2) if econ != "" else "", s["dot_balls"], s["catches"], s["stumpings"], s["run_outs"]])


if __name__ == "__main__":
    main()
