#!/usr/bin/env python3
"""Join the official RR 2026 squad to IPL 2025/2026 Cricsheet form rows.

Identity identifiers are pinned from the Cricsheet register to avoid fuzzy
name merges. A blank form row means no resolved record in the source archive.
"""
import argparse
import csv
from pathlib import Path

from train_model import load_deliveries, aggregate, combine, load_name_registry

ROSTER = [
    ("Dhruv Jurel", "Wicket-Keeper", "India", "bcf325d2"),
    ("Donovan Ferreira", "Wicket-Keeper", "South Africa", "f0af99a7"),
    ("Lhuan-dre Pretorius", "Wicket-Keeper", "South Africa", "60aa2db3"),
    ("Ravi Singh", "Wicket-Keeper", "India", "548516a6"),
    ("Aman Rao Perala", "Batter", "India", ""),
    ("Shimron Hetmyer", "Batter", "West Indies", "48a1d7b7"),
    ("Shubham Dubey", "Batter", "India", "6b2ff18f"),
    ("Vaibhav Sooryavanshi", "Batter", "India", "470f446b"),
    ("Yashasvi Jaiswal", "Batter", "India", "6c19c6e5"),
    ("Dasun Shanaka", "All-Rounder", "Sri Lanka", "3ff033bb"),
    ("Emanjot Chahal", "All-Rounder", "India", ""),
    ("Ravindra Jadeja", "All-Rounder", "India", "fe93fd9d"),
    ("Riyan Parag", "All-Rounder", "India", "04a418e8"),
    ("Yudhvir Singh", "All-Rounder", "India", "4885bbe6"),
    ("Adam Milne", "Bowler", "New Zealand", "350bb1b1"),
    ("Brijesh Sharma", "Bowler", "India", "133bbd61"),
    ("Jofra Archer", "Bowler", "England", "5574750c"),
    ("Kuldeep Sen", "Bowler", "India", "2e78f685"),
    ("Kwena Maphaka", "Bowler", "South Africa", "107c26fb"),
    ("Nandre Burger", "Bowler", "South Africa", "465aa633"),
    ("Ravi Bishnoi", "Bowler", "India", "df064e1a"),
    ("Sandeep Sharma", "Bowler", "India", "ce820073"),
    ("Sushant Mishra", "Bowler", "India", "92500ad5"),
    ("Tushar Deshpande", "Bowler", "India", "46a9bea1"),
    ("Vignesh Puthur", "Bowler", "India", "1e030637"),
    ("Yash Raj Punja", "Bowler", "India", "02dfebbe"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ipl-zip", default="work/data/ipl_csv2.zip")
    ap.add_argument("--people-csv", default="work/data/people.csv")
    ap.add_argument("--names-csv", default="work/data/names.csv")
    ap.add_argument("--out", default="outputs/rr_squad_form_2025_2026.csv")
    a = ap.parse_args()
    registry, _ = load_name_registry(a.people_csv, a.names_csv)
    deliveries = load_deliveries(a.ipl_zip)
    bat, _ = aggregate(deliveries, "bat", registry)
    bowl, _ = aggregate(deliveries, "bowl", registry)
    stats = combine(bat, bowl)
    fields = ["player", "official_role", "country", "roster_as_of", "season",
              "ipl_matches_with_bat_or_bowl", "runs", "batting_strike_rate",
              "batting_average", "wickets", "bowling_economy", "data_note"]
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for player, role, country, ident in ROSTER:
            for season in ("2025", "2026"):
                x = stats.get((season, ident), {}) if ident else {}
                w.writerow({
                    "player": player, "official_role": role, "country": country,
                    "roster_as_of": "RR official IPL 2026 squad page (checked 2026-11-07)",
                    "season": season,
                    "ipl_matches_with_bat_or_bowl": int(x.get("matches", 0)) if x else "",
                    "runs": int(x.get("runs", 0)) if x else "",
                    "batting_strike_rate": round(x.get("sr", 0), 2) if x else "",
                    "batting_average": round(x.get("bat_average", 0), 2) if x else "",
                    "wickets": int(x.get("wickets", 0)) if x else "",
                    "bowling_economy": round(x.get("econ", 0), 2) if x and x.get("bowl_balls") else "",
                    "data_note": "Cricsheet IPL Ashwin archive; blank means unresolved/missing, not zero",
                })
    print(f"Wrote {len(ROSTER)} roster players × 2 IPL seasons to {out_path}")


if __name__ == "__main__":
    main()
