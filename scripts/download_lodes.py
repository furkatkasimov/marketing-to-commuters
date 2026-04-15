"""
download_lodes.py
-----------------
Downloads LEHD Origin-Destination Employment Statistics (LODES) data
from the U.S. Census Bureau, including the origin-destination file
and the geographic crosswalk (which maps census blocks to lat/lon).

Dataset citation:
    U.S. Census Bureau, LEHD Origin-Destination Employment Statistics,
    https://lehd.ces.census.gov/data/lodes
"""

import os
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm


def download_file(url: str, dest: Path, chunk_size: int = 8192) -> Path:
    """Download a file with a progress bar. Returns the local path."""
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=dest.name
    ) as bar:
        for chunk in resp.iter_content(chunk_size):
            f.write(chunk)
            bar.update(len(chunk))
    return dest


def download_od_data(
    state: str,
    year: int,
    job_type: str = "JT00",
    version: str = "LODES8",
    base_url: str = "https://lehd.ces.census.gov/data/lodes",
    data_dir: str = "data",
) -> pd.DataFrame:
    """
    Download the LODES Origin-Destination (OD) main file for a state/year.

    The OD file contains columns:
      - w_geocode : 15-digit census block GEOID of the workplace
      - h_geocode : 15-digit census block GEOID of the residence (home)
      - S000      : total number of jobs for this home-to-work pair
      - SA01-SA03 : jobs by age group
      - SE01-SE03 : jobs by earnings bracket
      - SI01-SI03 : jobs by industry sector

    Returns a pandas DataFrame.
    """
    state = state.lower()
    filename = f"{state}_od_main_{job_type}_{year}.csv.gz"
    url = f"{base_url}/{version}/{state}/od/{filename}"
    local_gz = Path(data_dir) / filename

    if local_gz.exists():
        print(f"[OK] Already downloaded: {local_gz}")
    else:
        print(f"[DOWNLOADING] OD data: {url}")
        download_file(url, local_gz)

    print("[LOADING] Reading OD data into DataFrame ...")
    df = pd.read_csv(
        local_gz,
        dtype={"w_geocode": str, "h_geocode": str},
        compression="gzip",
    )
    print(f"[OK] Loaded {len(df):,} origin-destination pairs.")
    return df


def download_crosswalk(
    state: str,
    version: str = "LODES8",
    base_url: str = "https://lehd.ces.census.gov/data/lodes",
    data_dir: str = "data",
) -> pd.DataFrame:
    """
    Download the LODES Geographic Crosswalk for a state.

    The crosswalk maps every census block to its lat/lon and to higher-
    level geographies (county, tract, ZCTA / zip code, etc.).

    Key columns:
      - tabblk2020 : 15-digit census block GEOID (join key)
      - blklatdd   : latitude of the block centroid
      - blklondd   : longitude of the block centroid
      - zcta       : ZIP Code Tabulation Area
      - cty        : county FIPS code
    """
    state = state.lower()
    filename = f"{state}_xwalk.csv.gz"
    url = f"{base_url}/{version}/{state}/{filename}"
    local_gz = Path(data_dir) / filename

    if local_gz.exists():
        print(f"[OK] Already downloaded: {local_gz}")
    else:
        print(f"[DOWNLOADING] Crosswalk: {url}")
        download_file(url, local_gz)

    print("[LOADING] Reading crosswalk ...")
    df = pd.read_csv(
        local_gz,
        dtype={"tabblk2020": str, "zcta": str, "cty": str},
        usecols=["tabblk2020", "blklatdd", "blklondd", "zcta", "cty"],
        compression="gzip",
    )
    print(f"[OK] Loaded crosswalk with {len(df):,} census blocks.")
    return df


def build_commuter_locations(
    od: pd.DataFrame, xwalk: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge OD data with the crosswalk to get lat/lon for both the home
    and work census block of every commuter pair.

    Returns a DataFrame with columns:
      h_geocode, w_geocode, S000 (job count),
      h_lat, h_lon (home centroid),
      w_lat, w_lon (work centroid),
      h_zcta, w_zcta (ZIP codes)
    """
    print("[MERGING] Adding home locations ...")
    merged = od.merge(
        xwalk.rename(
            columns={
                "tabblk2020": "h_geocode",
                "blklatdd": "h_lat",
                "blklondd": "h_lon",
                "zcta": "h_zcta",
            }
        )[["h_geocode", "h_lat", "h_lon", "h_zcta"]],
        on="h_geocode",
        how="inner",
    )

    print("[MERGING] Adding work locations ...")
    merged = merged.merge(
        xwalk.rename(
            columns={
                "tabblk2020": "w_geocode",
                "blklatdd": "w_lat",
                "blklondd": "w_lon",
                "zcta": "w_zcta",
            }
        )[["w_geocode", "w_lat", "w_lon", "w_zcta"]],
        on="w_geocode",
        how="inner",
    )

    # Keep only rows where home != work (actual commuters)
    merged = merged[
        (merged["h_lat"] != merged["w_lat"])
        | (merged["h_lon"] != merged["w_lon"])
    ].copy()

    print(f"[OK] {len(merged):,} commuter pairs with coordinates.")
    return merged[
        [
            "h_geocode", "w_geocode", "S000",
            "h_lat", "h_lon", "h_zcta",
            "w_lat", "w_lon", "w_zcta",
        ]
    ]


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    lodes_cfg = cfg["lodes"]
    od = download_od_data(
        state=lodes_cfg["state"],
        year=lodes_cfg["year"],
        job_type=lodes_cfg["job_type"],
        version=lodes_cfg["version"],
        base_url=lodes_cfg["base_url"],
    )
    xwalk = download_crosswalk(
        state=lodes_cfg["state"],
        version=lodes_cfg["version"],
        base_url=lodes_cfg["base_url"],
    )
    commuters = build_commuter_locations(od, xwalk)
    out_path = Path(cfg["output"]["directory"]) / "commuter_pairs.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    commuters.to_csv(out_path, index=False)
    print(f"[OK] Saved commuter pairs to {out_path}")
