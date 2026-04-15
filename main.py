"""
main.py
-------
Marketing to Commuters — Full Pipeline

Runs all steps in sequence:
  1. Download LODES origin-destination data from the U.S. Census Bureau
  2. Compute driving routes for top commuter pairs
  3. Identify commuters whose routes pass near the target business
  4. Generate an interactive HTML map

Usage:
    python main.py                        # uses config.yaml defaults
    python main.py --state va --year 2022 # override state and year
    python main.py --help                 # see all options
"""

import sys
from pathlib import Path

import click
import yaml

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from download_lodes import download_od_data, download_crosswalk, build_commuter_locations
from analyze_commutes import analyze_commuters
from generate_map import generate_map


@click.command()
@click.option("--config", default="config.yaml", help="Path to config YAML file.")
@click.option("--state", default=None, help="Override state (e.g. 'va', 'dc').")
@click.option("--year", default=None, type=int, help="Override data year.")
@click.option("--business-lat", default=None, type=float, help="Override business latitude.")
@click.option("--business-lon", default=None, type=float, help="Override business longitude.")
@click.option("--max-routes", default=None, type=int, help="Override max routes to compute.")
@click.option("--skip-download", is_flag=True, help="Skip download if data already exists.")
def run(config, state, year, business_lat, business_lon, max_routes, skip_download):
    """Marketing to Commuters — full pipeline."""

    with open(config) as f:
        cfg = yaml.safe_load(f)

    # Apply CLI overrides
    if state:
        cfg["lodes"]["state"] = state
    if year:
        cfg["lodes"]["year"] = year
    if business_lat:
        cfg["business"]["latitude"] = business_lat
    if business_lon:
        cfg["business"]["longitude"] = business_lon
    if max_routes:
        cfg["routing"]["max_routes"] = max_routes

    lodes_cfg = cfg["lodes"]
    biz_cfg = cfg["business"]
    routing_cfg = cfg["routing"]
    out_dir = Path(cfg["output"]["directory"])
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  MARKETING TO COMMUTERS")
    print("=" * 60)
    print(f"  State        : {lodes_cfg['state'].upper()}")
    print(f"  Year         : {lodes_cfg['year']}")
    print(f"  Business     : {biz_cfg['name']}")
    print(f"  Location     : {biz_cfg['latitude']}, {biz_cfg['longitude']}")
    print(f"  Buffer       : {biz_cfg['buffer_meters']}m ({biz_cfg['buffer_meters'] / 1609.34:.1f} miles)")
    print(f"  Routing      : {routing_cfg['engine']}")
    print(f"  Max routes   : {routing_cfg['max_routes']}")
    print("=" * 60)

    # --- Step 1: Download LODES data ---
    commuter_csv = out_dir / "commuter_pairs.csv"
    if skip_download and commuter_csv.exists():
        print("\n[1/3] Skipping download — using existing commuter_pairs.csv")
        import pandas as pd
        commuters = pd.read_csv(
            commuter_csv,
            dtype={"h_geocode": str, "w_geocode": str, "h_zcta": str, "w_zcta": str},
        )
    else:
        print("\n[1/3] Downloading LODES data from Census Bureau ...")
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
        commuters.to_csv(commuter_csv, index=False)

    # --- Step 2: Route analysis ---
    print("\n[2/3] Computing driving routes and checking proximity ...")
    passing = analyze_commuters(
        commuters,
        business_lat=biz_cfg["latitude"],
        business_lon=biz_cfg["longitude"],
        buffer_meters=biz_cfg["buffer_meters"],
        routing_engine=routing_cfg["engine"],
        osrm_url=routing_cfg.get("osrm_url", ""),
        google_api_key=routing_cfg.get("google_api_key", ""),
        max_routes=routing_cfg["max_routes"],
        request_delay=routing_cfg["request_delay"],
    )

    if passing.empty:
        print("\n[!] Pipeline stopped — no matching commuters found.")
        print("    Try increasing buffer_meters or max_routes in config.yaml.")
        return

    passing.drop(columns=["route_geometry"]).to_csv(
        out_dir / "commuters_passing_business.csv", index=False
    )
    passing.to_file(
        out_dir / "commuters_passing_business.geojson", driver="GeoJSON"
    )

    # --- Step 3: Generate map ---
    if cfg["output"].get("html_map", True):
        print("\n[3/3] Generating interactive map ...")
        generate_map(
            business_name=biz_cfg["name"],
            business_lat=biz_cfg["latitude"],
            business_lon=biz_cfg["longitude"],
            routes_geojson=str(out_dir / "commuters_passing_business.geojson"),
            output_html=str(out_dir / "commuter_map.html"),
        )

    # --- Summary ---
    print("\n" + "=" * 60)
    print(f"  DONE!")
    print(f"  Commuter pairs analyzed : {routing_cfg['max_routes']}")
    print(f"  Routes passing business : {len(passing)}")
    print(f"  Output directory        : {out_dir}/")
    print("=" * 60)
    print("\nOutput files:")
    for f in sorted(out_dir.glob("*")):
        print(f"  - {f}")


if __name__ == "__main__":
    run()
