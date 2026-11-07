#!/usr/bin/env python3
"""Export the trained sklearn pipelines as compact browser inference params."""
import argparse
import json
from pathlib import Path

import joblib


def pipeline_params(pipeline):
    scaler = pipeline.named_steps["standardscaler"]
    estimator = pipeline.steps[-1][1]
    return {
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coef": estimator.coef_.reshape(-1).tolist(),
        "intercept": float((estimator.intercept_ if getattr(estimator, "intercept_", None) is not None else estimator.intercept).reshape(-1)[0]),
    }


def export(model_path):
    model = joblib.load(model_path)
    return {
        "features": model["features"],
        "appearance": pipeline_params(model["appearance_model"]),
        "impact": pipeline_params(model["impact_model"]),
        "label_definition": model["label_definition"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--multi", required=True)
    parser.add_argument("--smat", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--dashboard", default="index.html")
    parser.add_argument("--mirror", default="outputs/superrr-scout-dashboard.html")
    args = parser.parse_args()
    output = {"multi": export(args.multi), "smat": export(args.smat), "rank_blend": 0.5}
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(output, separators=(",", ":"))
    path.write_text(serialized)
    for dashboard_path in (Path(args.dashboard), Path(args.mirror)):
        if not dashboard_path.exists():
            continue
        html = dashboard_path.read_text()
        marker = "const modelParams="
        start = html.index(marker) + len(marker)
        end = html.index(";\nfunction norm", start)
        dashboard_path.write_text(html[:start] + serialized + html[end:])
    print(f"Wrote browser model parameters to {path}")


if __name__ == "__main__":
    main()
