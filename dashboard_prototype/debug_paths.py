from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_DIST = BASE_DIR / "data_dist"
HIST_PATH = BASE_DIR.parent / "data" / "processed" / "historico"

print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIST: {DATA_DIST}")
print(f"HIST_PATH: {HIST_PATH}")

available_years = sorted([int(f.stem.split('_')[1]) for f in HIST_PATH.glob("profiles_*.parquet")])
print(f"Años: {available_years}")

for year in available_years:
    path = DATA_DIST / f"year_{year}.json"
    print(f"Probando abrir: {path}")
    try:
        with open(path, 'w') as f:
            f.write("{}")
        print("  OK")
    except Exception as e:
        print(f"  ERROR: {e}")
