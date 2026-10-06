"""Validate the actual house SERIES on both supported surfaces, not a copied palette."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "visualization-curriculum"))
import house_style
from check_palette import check


def main():
    passed = True
    for background in (house_style.PAPER, "#FFFFFF"):
        report = check(house_style.SERIES, bg=background)
        worst = min(item["min_delta_e"] for item in report["separation"].values())
        print(f"{background}: {'PASS' if report['ok'] else 'FAIL'}; worst simulated separation = {worst}")
        passed &= report["ok"]
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
